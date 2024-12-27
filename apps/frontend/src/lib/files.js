export function formatFileSize(size) {
  return `${(size / 1024 / 1024).toFixed(2)} MB`;
}

export function getCsvHeadersColumns(file, onSuccess) {
  const reader = new FileReader();
  reader.onload = (e) => {
    const text = e.target.result;
    const firstLine = text.split('\n')[0];
    const headers = firstLine.split(',').map(header => header.trim());
    const rowCount = text.split('\n').length - 1; // -1 to exclude header row
    console.log('Number of rows:', rowCount);
    console.log('CSV Headers:', headers);
    onSuccess(headers, rowCount);
  };
  reader.onerror = (e) => {
    console.error('Error reading file:', e);
  };
  reader.readAsText(file);
}