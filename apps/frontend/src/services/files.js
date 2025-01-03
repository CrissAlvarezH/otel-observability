import { trace, SpanStatusCode, context } from "@opentelemetry/api"

import { API_DOMAIN } from "../lib/config";

export const DEFAULT_PART_SIZE = 5;


const tracer = trace.getTracer("frontend")

/**
 * Upload a file by parts to S3.
 * @param file - The file to upload.
 * @param options - The options for the upload.
 * @param options.batchSize - The batch size for the upload. Defaults to the number of parts.
 * @param options.partSize - The size of each part to upload. Defaults to 5MB.
 * @param options.onProgress - A callback function that will be called with the progress of the upload.
 * @param options.token - The token to use for the upload.
 */
export async function uploadFileByParts({ file, columns, rowCount }, { batchSize, partSize = DEFAULT_PART_SIZE, onProgress, token } = {}) {
  const span = tracer.startSpan("upload-file", { root: true })
  span.setAttributes({ "file.name": file.name, "file.size": file.size, "file.columns": columns, "file.rows": rowCount })
  const ctx = trace.setSpan(context.active(), span)

  try {
    const { uploadId, fileId, traceHeaders } = await context.with(ctx, initUpload, undefined, file, columns, rowCount, token);

    const uploadPartJobs = [];
    const partSizeInMB = partSize * 1024 * 1024;
    const totalParts = Math.ceil(file.size / partSizeInMB);
    const partResults = [];

    for (let partNumber = 1; partNumber <= totalParts; partNumber++) {
      uploadPartJobs.push(async () => {
        const jobSpan = tracer.startSpan("job-upload-part-" + partNumber, {}, ctx)
        const jobCtx = trace.setSpan(ctx, jobSpan)

        const part = file.slice((partNumber - 1) * partSizeInMB, partNumber * partSizeInMB);

        const url = await context.with(jobCtx, getPresignedUrl, undefined, file, uploadId, partNumber, token, traceHeaders);

        const etag = await context.with(jobCtx, uploadPart, undefined, url, part);

        partResults.push({
          PartNumber: partNumber,
          ETag: etag,
        });

        // We don't want to show 100% progress because is missing the call to /complete
        const progress = Math.min(99, Math.floor(partResults.length / totalParts * 100));
        onProgress?.(progress);
        jobSpan.end()
      });
    }

    const batchLength = batchSize ?? uploadPartJobs.length;
    for (let i = 0; i < uploadPartJobs.length; i += batchLength) {
      const batch = uploadPartJobs.slice(i, i + batchLength);
      await Promise.all(batch.map(job => job()))
    }

    await context.with(ctx, completeUpload, undefined, file.name, fileId, uploadId, partResults, token, traceHeaders);
    onProgress?.(100);
    span.end()
  } catch (error) {
    span.setStatus(SpanStatusCode.ERROR)
    span.setAttribute("error", error.message)
    span.end()
    throw error
  }
}

async function initUpload(file, columns, rowCount, token) {
  const span = tracer.startSpan("init-upload")

  return context.with(trace.setSpan(context.active(), span), async () => {
    const initRes = await fetch(`${API_DOMAIN}/upload/init`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Token": token },
      body: JSON.stringify({
        filename: file.name,
        file_size: file.size,
        columns: columns,
        row_count: rowCount,
      }),
    });
    if (!initRes.ok) {
      let error = new Error("Failed to initialize multipart upload");
      if (initRes.status === 401) {
        error = new Error("Unauthorized");
      } 

      span.setStatus(SpanStatusCode.ERROR)
      span.recordException(error)
      span.end()
      throw error
    }
    const traceHeaders = {}
    if (initRes.headers.has("traceparent"))
      traceHeaders["traceparent"] = initRes.headers.get("traceparent")
    if (initRes.headers.has("tracestate"))
      traceHeaders["tracestate"] = initRes.headers.get("tracestate")

    const { upload_id: uploadId, file_id: fileId } = await initRes.json();

    span.end()
    return { uploadId, fileId, traceHeaders };
  })
}

async function uploadPart(url, part) {
  const span = tracer.startSpan("upload-part")

  return context.with(trace.setSpan(context.active(), span), async () => {
    const uploadRes = await fetch(url, {
      method: "PUT",
      body: part,
    });
    if (!uploadRes.ok) {
      span.setStatus(SpanStatusCode.ERROR)
      if (uploadRes.status === 401) {
        span.setAttribute("error", "Unauthorized")
        span.end()
        throw new Error("Unauthorized");
      }
      span.setAttribute("error", "Failed init upload")
      span.end()
      throw new Error("Failed to upload part");
    }

    span.end()
    return uploadRes.headers.get("ETag");
  })
}

async function getPresignedUrl(file, uploadId, partNumber, token, traceHeaders) {
  const span = tracer.startSpan("get-presigned-url")

  return context.with(trace.setSpan(context.active(), span), async () => {
    const presignedRes = await fetch(`${API_DOMAIN}/upload/get-presigned-url`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Token": token, ...traceHeaders },
      body: JSON.stringify({
        filename: file.name,
        upload_id: uploadId,
        part_number: partNumber,
      }),
    });
    if (!presignedRes.ok) {
      span.setStatus(SpanStatusCode.ERROR)
      if (presignedRes.status === 401) {
        span.setAttribute("error", "Unauthorized")
        span.end()
        throw new Error("Unauthorized");
      }
      span.setAttribute("error", "Failed to get presigned url")
      span.end()
      throw new Error("Failed to get presigned url");
    }
    const { url } = await presignedRes.json();

    span.end()
    return url;
  })
}

async function completeUpload(fileName, fileId, uploadId, partResults, token, traceHeaders) {
  const span = tracer.startSpan("complete-upload")

  await context.with(trace.setSpan(context.active(), span), async () => {
    const completeRes = await fetch(`${API_DOMAIN}/upload/complete`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Token": token, ...traceHeaders },
      body: JSON.stringify({
        file_id: fileId,
        filename: fileName,
        upload_id: uploadId,
        // parts must be sorted by part number
        parts: partResults.sort((a, b) => a.PartNumber - b.PartNumber),
      }),
    });
    if (!completeRes.ok) {
      if (completeRes.status === 401) {
        span.setAttribute("error", "Unauthorized")
        span.end()
        throw new Error("Unauthorized");
      }
      span.setAttribute("error", "Failed to complete multipart upload")
      span.end()
      throw new Error("Failed to complete multipart upload");
    }

    span.end()
  })
}

export async function fetchUploadedFiles() {
  const res = await fetch(`${API_DOMAIN}/files`);
  if (!res.ok) {
    throw new Error("Failed to fetch uploaded files");
  }
  return res.json();
}