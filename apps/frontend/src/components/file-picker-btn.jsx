import { useState } from "react";
import { useRef } from "react";
import { getCsvHeadersColumns } from "../lib/files";

export function FilePickerButton({
	className,
	onSelectFile,
}) {
	const fileInputRef = useRef(null);
	const [error, setError] = useState(null);

	const handleFileChange = (event) => {
		const file = event.target.files?.[0];
		if (file) {
			getCsvHeadersColumns(file, (headers, rowCount) => {
				onSelectFile({ file, headers, rowCount });
				setError(null);
			});
		} else {
			setError("No file selected");
		}
	};

	const handleUpload = () => {
		fileInputRef.current?.click();
	};

	return (
		<>
			{error && <p className="text-red-500">{error}</p>}

			<input
				ref={fileInputRef}
				type="file"
				accept=".csv"
				className="hidden"
				onChange={handleFileChange}
			/>

			<button
				onClick={handleUpload}
				className={"block font-semibold bg-black text-white px-4 py-2 rounded-md " + className}
			>
				Select file
			</button>
		</>
	);
}