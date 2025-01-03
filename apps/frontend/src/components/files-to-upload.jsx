import { useState } from "react";

import { uploadFileByParts } from "../services/files";
import { CloudDone, BackspaceIcon, UploadIcon } from "./icons";
import { Spinner } from "./icons";
import { formatFileSize } from "../lib/files";


export function FileToUpload({ file, uploadConfig, onRemove, onUploadSuccess, onUploadError }) {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const handleUpload = async (file) => {
    setIsUploading(true);

    uploadFileByParts({
      file: file.file,
      columns: file.headers,
      rowCount: file.rowCount,
    }, {
      batchSize: uploadConfig?.batchSize,
      partSize: uploadConfig?.partSize,
      token: uploadConfig?.token,
      onProgress: setUploadProgress
    })
      .then(() => {
        onUploadSuccess();
      })
      .catch((error) => {
        onUploadError(error);
      })
      .finally(() => {
        setIsUploading(false);
      });
  };

  return (
    <div className="bg-white shadow-md rounded-lg py-4 px-6 border flex items-center justify-between gap-10 min-w-[300px]">
      <div>
        <p className="font-medium text-gray-800 truncate">{file.file.name}</p>
        {file.uploadError && (
          <p className="text-red-500 text-sm max-w-56">
            Error: {file.uploadError.message}
          </p>
        )}
        <p className="text-gray-500 text-xs pt-1">Columns:</p>
        <p
          className="text-gray-500 text-xs border px-1 bg-gray-100/50 rounded truncate text-ellipsis"
          title={file.headers.join(', ')}>
          {file.headers.join(', ').slice(0, 50) + "..."}
        </p>

        <div className="flex gap-1.5 items-baseline">
          <p className="text-gray-500 text-sm">{file.rowCount} rows</p>
          <p className="text-gray-400 font-extralight">|</p>
          <p className="text-gray-500 text-sm">{formatFileSize(file.file.size)}</p>
        </div>
      </div>


      <div className="flex gap-0.5">

        {file.isUploaded ? (
          <div className="p-2">
            <CloudDone className="fill-green-600" />
          </div>
        ) : (
          <>
            <button
              id="btn-upload-file"
              className="hover:bg-gray-100 rounded-md p-2 transition-colors"
              onClick={() => handleUpload(file)}
              disabled={isUploading}
            >
              {isUploading ? (
                <div className="flex items-center gap-1">
                  <p className="text-sm text-blue-600">{uploadProgress}%</p>
                  <Spinner className="fill-blue-600" />
                </div>
              ) : (
                <UploadIcon className="fill-blue-600" />
              )}
            </button>

            <button
              className="p-2 hover:bg-red-50 hover:fill-red-600 disabled:opacity-50 rounded-md transition-colors"
              onClick={onRemove}
              disabled={isUploading}
            >
              <BackspaceIcon className="fill-red-600" />
            </button>
          </>
        )}
      </div>
    </div>
  )
}