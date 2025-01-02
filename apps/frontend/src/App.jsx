import { useState } from 'react'
import { FilePickerButton } from './components/file-picker-btn';
import { ConfigForm } from './components/config-form';
import { FileToUpload } from './components/files-to-upload';
import { UploadedFiles } from './components/uploaded-files';

import "./instrumentation/otel"


export default function App() {
  const [files, setFiles] = useState([]);
  const [refreshUploads, setRefreshUploads] = useState(false);
  const [uploadBatchSize, setUploadBatchSize] = useState();
  const [uploadPartSize, setUploadPartSize] = useState();
  const [token, setToken] = useState();

  const handleSelectFile = (data) => {
    setFiles([...files, { file: data.file, headers: data.headers, rowCount: data.rowCount }]);
  };

  const handleRemoveFile = (file) => {
    setFiles(files.filter(f => f.file.name !== file.file.name));
  };

  const handleUploadSuccess = (file) => {
    setFiles(files.map(f => f.file.name !== file.file.name ? f : { ...f, isUploaded: true, uploadError: null }));
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

          <ConfigForm
            token={token}
            setToken={setToken}
            uploadBatchSize={uploadBatchSize}
            setUploadBatchSize={setUploadBatchSize}
            uploadPartSize={uploadPartSize}
            setUploadPartSize={setUploadPartSize}
          />

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
