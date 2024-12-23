import { useState, useEffect } from 'react'
import { uploadFileByParts, fetchUploadedFiles } from './services/files';
import { formatFileSize } from './lib/files';
import { FilePickerButton } from './components/file-picker-btn';
import { BackspaceIcon, CloudDone, Spinner, UploadIcon, CopyIcon, DoneIcon } from './components/icons';
import { getTokens } from './services/tokens';


export default function App() {
  const [files, setFiles] = useState([]);
  const [refreshUploads, setRefreshUploads] = useState(false);
  const [uploadBatchSize, setUploadBatchSize] = useState();
  const [uploadPartSize, setUploadPartSize] = useState();
  const [token, setToken] = useState();
  const handleSelectFile = (file) => {
    setFiles([...files, { file }]);
  };

  const handleRemoveFile = (file) => {
    setFiles(files.filter(f => f.file.name !== file.file.name));
  };

  const handleUploadSuccess = (file) => {
    setFiles(files.map(f => f.file.name !== file.file.name ? f : { ...f, isUploaded: true }));
    setRefreshUploads(prev => !prev);
  };

  const handleUploadError = (file, error) => {
    setFiles(files.map(f => f.file.name !== file.file.name ? f : { ...f, uploadError: error }));
    setRefreshUploads(prev => !prev);
  };

  return (
    <>
      <h1 className="text-xl text-center shadow text-gray-800 border-b p-3 font-bold">Upload File to S3</h1>

      <div className="flex justify-center px-4">

        <div className="flex w-full items-start max-w-4xl py-5 gap-4">

          <div className="flex-1 bg-gray-100 rounded-lg p-4 space-y-2">
            <h1 className="text-xl font-bold text-gray-800">Configurations</h1>
            <div>
              <p className="text-sm text-gray-500">Token</p>
              <input
                type="text"
                value={token}
                placeholder="User token"
                className="border border-gray-300 rounded-md p-2 w-full"
                onChange={(e) => setToken(e.target.value)}
              />
            </div>

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

            <Tokens />
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
                  uploadConfig={{ batchSize: uploadBatchSize, partSize: uploadPartSize, token }}
                  onRemove={() => handleRemoveFile(file)}
                  onUploadSuccess={() => handleUploadSuccess(file)}
                  onUploadError={(error) => handleUploadError(file, error)}
                />
              ))}
            </div>

            <UploadedFiles refreshUploads={refreshUploads} />

          </div>

        </div>
      </div>
    </>
  );
}

function UploadedFiles({ refreshUploads }) {
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    setIsLoading(true);
    fetchUploadedFiles()
      .then(res => setUploadedFiles(res.result))
      .catch(setError)
      .finally(() => setIsLoading(false));
  }, [refreshUploads]);

  return (
    <div>
      <div className="flex items-center gap-2 pb-2">
        <h1 className="text-xl font-bold">Uploaded Files</h1>
        {isLoading && (
          <Spinner className="fill-blue-600 w-5 h-5" />
        )}
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
          </>
        )}
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

function Tokens() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [tokens, setTokens] = useState([]);

  const [copiedToken, setCopiedToken] = useState(null);

  useEffect(() => {
    getTokens().then(setTokens);
  }, []);

  const handleCopyToken = (token) => {
    navigator.clipboard.writeText(token);
    setCopiedToken(token);
    setTimeout(() => setCopiedToken(null), 2000);
  };

  return (
    <div>
      <h1 className="text-xl font-bold py-2">Tokens</h1>
      {isLoading && (
        <div className="flex items-center gap-2">
          <Spinner className="fill-blue-600 w-5 h-5" />
          <p className="text-sm">Loading tokens...</p>
        </div>
      )}

      <div className="flex flex-col bg-white rounded">
        {tokens.map((token) => (
          <div key={token.token} className="border-y px-3 py-2">
            <p className="text-medium font-semibold">{token.username}</p>

            <div className="flex items-center justify-between bg-gray-100 rounded-md p-1">
              <p className="text-sm px-1 text-gray-800 font-light font-mono">{token.token}</p>
              <button onClick={() => handleCopyToken(token.token)} className="hover:bg-gray-200 p-1 rounded-md">
                {copiedToken === token.token ? (
                  <DoneIcon className="w-4 h-4" />
                ) : (
                  <CopyIcon className="fill-gray-600 w-4 h-4" />
                )}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}