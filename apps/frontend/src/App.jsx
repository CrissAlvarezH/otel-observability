import { useState, useEffect } from 'react'
import { uploadFileByParts, fetchUploadedFiles } from './services/files';
import { formatFileSize } from './lib/files';
import { FilePickerButton } from './components/file-picker-btn';
import { BackspaceIcon, CloudDone, Spinner, UploadIcon } from './components/icons';


export default function App() {
  const [files, setFiles] = useState([]);
  const [uploadBatchSize, setUploadBatchSize] = useState();
  const [uploadPartSize, setUploadPartSize] = useState();

  const handleSelectFile = (file) => {
    setFiles([...files, { file }]);
  };

  const handleRemoveFile = (file) => {
    setFiles(files.filter(f => f.file.name !== file.file.name));
  };

  const handleUploadSuccess = (file) => {
    setFiles(files.map(f => f.file.name !== file.file.name ? f : { ...f, isUploaded: true }));
  };

  const handleUploadError = (file, error) => {
    setFiles(files.map(f => f.file.name !== file.file.name ? f : { ...f, uploadError: error }));
  };

  return (
    <>
      <h1 className="text-xl text-center shadow text-gray-800 border-b p-3 font-bold">Upload File to S3</h1>

      <div className="flex justify-center px-4">

        <div className="flex w-full items-start max-w-4xl py-5 gap-4">

          <div className="flex-1 bg-gray-100 rounded-lg p-4 space-y-2">
            <h1 className="text-xl font-bold text-gray-800">Configurations</h1>
            <div>
              <p className="text-sm text-gray-500">Batch size (simultaneous uploads)</p>
              <input
                type="number"
                value={uploadBatchSize?.toString() || ""}
                placeholder="Empty for unlimited"
                className="border border-gray-300 rounded-md p-2 w-full"
                onChange={(e) => setUploadBatchSize(e.target.value ? parseInt(e.target.value) : undefined)}
              />
            </div>

            <div>
              <p className="text-sm text-gray-500">Part size (MB)</p>
              <input
                type="number"
                value={uploadPartSize?.toString() || ""}
                placeholder="Default 5MB"
                className="border border-gray-300 rounded-md p-2 w-full"
                onChange={(e) => setUploadPartSize(e.target.value ? parseInt(e.target.value) : undefined)}
              />
            </div>
          </div>

          <div className="flex-[2]">
            <FilePickerButton
              className="w-full"
              onSelectFile={handleSelectFile}
            />

            <h1 className="text-xl font-bold pt-2">Files to upload</h1>

            <div className="flex flex-col gap-2 pt-3 pb-4 min-h-20 justify-center">
              {files.length === 0 && (
                <p className="text-gray-500 text-center">No files selected</p>
              )}

              {files.map((file) => (
                <FileToUpload
                  key={file.file.name}
                  file={file}
                  uploadConfig={{ batchSize: uploadBatchSize, partSize: uploadPartSize }}
                  onRemove={() => handleRemoveFile(file)}
                  onUploadSuccess={() => handleUploadSuccess(file)}
                  onUploadError={(error) => handleUploadError(file, error)}
                />
              ))}
            </div>

            <UploadedFiles />

          </div>

        </div>
      </div>
    </>
  );
}

function UploadedFiles() {
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    setIsLoading(true);
    fetchUploadedFiles()
      .then(res => setUploadedFiles(res.result))
      .finally(() => setIsLoading(false));
  }, []);

  return (
    <div>
      <div className="flex items-center gap-2 pb-2">
        <h1 className="text-xl font-bold">Uploaded Files</h1>
        {isLoading && (
          <Spinner className="fill-blue-600 w-5 h-5" />
        )}
      </div>

      <div className="flex flex-col gap-2">
        {uploadedFiles.map((file) => (
          <div key={file.id} className="bg-white shadow-md rounded-lg py-4 px-6 border flex items-start justify-between gap-10">
            <div>
              <p className="font-medium text-gray-800 truncate">{file.filename}</p>
              <div className="flex gap-2">
                <p className="text-gray-500 text-sm">{formatFileSize(file.file_size)}</p>
                <p className="font-light text-sm">{file.creation_datetime}</p>
              </div>
            </div>
            <p className="self-start text-gray-500 text-xs capitalize">{file.status}</p>
          </div>
        ))}
      </div>
    </div >
  )
}

function FileToUpload({ file, uploadConfig, onRemove, onUploadSuccess, onUploadError }) {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const handleUpload = async (file) => {
    setIsUploading(true);

    uploadFileByParts(file.file, {
      batchSize: uploadConfig?.batchSize,
      partSize: uploadConfig?.partSize,
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
        <p className="text-gray-500 text-sm">{formatFileSize(file.file.size)}</p>
      </div>

      {file.uploadError && (
        <p className="text-red-500 text-sm max-w-56">
          Error: {file.uploadError.message}
        </p>
      )}

      <div className="flex gap-0.5">

        {file.isUploaded ? (
          <div className="p-2">
            <CloudDone className="fill-green-600" />
          </div>
        ) : (
          <>
            <button
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
