import { useState } from "react";
import { useRef } from "react";

export function FilePickerButton({
	className,
	onSelectFile,
}) {
	const fileInputRef = useRef(null);
	const [error, setError] = useState(null);

	const handleFileChange = (event) => {
		const file = event.target.files?.[0];
		if (file) {
			onSelectFile(file);
			setError(null);
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