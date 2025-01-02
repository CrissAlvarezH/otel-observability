import { useState, useEffect } from "react";

import { fetchUploadedFiles } from "../services/files";
import { formatFileSize } from "../lib/files";
import { Spinner, RefreshIcon } from "./icons";


export function UploadedFiles({ refreshUploads }) {
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    callUploadedFiles();
  }, [refreshUploads]);

  const callUploadedFiles = () => {
    setError(null);
    setIsLoading(true);
    fetchUploadedFiles()
      .then(res => setUploadedFiles(res.result))
      .catch(setError)
      .finally(() => setIsLoading(false));
  }

  return (
    <div>
      <div className="flex justify-between items-center gap-2 pb-2">
        <h1 className="text-xl font-bold">Uploaded Files</h1>

        <button
          className="p-1 bg-blue-100/50 rounded-full hover:bg-blue-100 transition-colors"
          disabled={isLoading}
          onClick={() => callUploadedFiles()}
        >
          {isLoading ? <Spinner className="fill-blue-600 w-5 h-5 m-0.5" /> : <RefreshIcon className="fill-blue-600 w-6 h-6" />}
        </button>
      </div>

      <div className="flex flex-col gap-2">

        {error ? (
          <p className="text-red-500 text-center">Error: {error.message}</p>
        ) : (
          <>
            {!isLoading && uploadedFiles.length === 0 && (
              <p className="text-gray-500 text-center">No files uploaded</p>
            )}

            {uploadedFiles.map((file) => (
              <div key={file.id} className="bg-white shadow-md rounded-lg py-4 px-6 border flex items-start justify-between gap-10">
                <div className="space-y-0.5">
                  <div className="flex items-baseline gap-3">
                    <p className="font-medium text-gray-800 truncate">{file.filename}</p>
                    <p className="text-xs border border-gray-300 px-2 rounded-md">{file.username}</p>
                  </div>

                  <p className="text-gray-500 text-xs pt-1">Columns:</p>
                  <p
                    className="text-gray-500 text-xs inline-block border px-1 bg-gray-100/50 rounded truncate text-ellipsis"
                    title={file.columns.join(', ')}>
                    {file.columns.join(', ').slice(0, 50) + "..."}
                  </p>

                  <div className="flex gap-1.5 items-baseline">
                    <p className="text-gray-500 text-sm">{file.row_count} rows</p>
                    <p className="text-gray-400 font-extralight">|</p>
                    <p className="text-gray-500 text-sm">{formatFileSize(file.file_size)}</p>
                    <p className="text-gray-400 font-extralight">|</p>
                    <p className="font-light text-sm">{file.creation_datetime}</p>
                  </div>
                </div>

                <p className="text-gray-500 text-xs capitalize">{file.status}</p>
              </div>
            ))}
          </>
        )}
      </div>
    </div >
  )
}
