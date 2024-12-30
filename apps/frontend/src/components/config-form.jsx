import { useState, useEffect } from "react";

import { getTokens } from "../services/tokens";
import { Spinner } from "./icons";


export function ConfigForm({ token, setToken, uploadBatchSize, setUploadBatchSize, uploadPartSize, setUploadPartSize }) {
  return (
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
  )
} 


function Tokens() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [tokens, setTokens] = useState([]);

  useEffect(() => {
    setIsLoading(true);
    getTokens()
      .then(setTokens)
      .catch(setError)
      .finally(() => setIsLoading(false));
  }, []);

  return (
    <div>
      <h1 className="text-xl font-bold py-2">Tokens</h1>

      {isLoading && (
        <div className="flex items-center gap-2">
          <Spinner className="fill-blue-600 w-5 h-5" />
          <p className="text-sm">Loading tokens...</p>
        </div>
      )}

      {error && (
        <p className="text-red-500 text-center">Error: {error.message}</p>
      )}

      <div className="flex flex-col bg-white rounded">
        {!isLoading && !error && tokens.length === 0 && (
          <p className="text-gray-500 py-4 text-center">No tokens found</p>
        )}

        {tokens.map((token) => (
          <div key={token.token} className="border-y px-3 py-2">
            <p className="text-medium font-semibold">{token.username}</p>

            <div className="flex items-center justify-between bg-gray-100 rounded-md p-1">
              <p className="text-sm px-1 text-gray-800 font-light font-mono">{token.token}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}