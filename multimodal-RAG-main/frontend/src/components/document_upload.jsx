import React, { useState } from 'react';
import { api } from '../services/api';

const DocumentUpload = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('idle'); // 'idle' | 'uploading' | 'success' | 'error'
  const [result, setResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      
      // Basic validation
      if (file.type !== 'application/pdf') {
        setErrorMessage('Please select a valid PDF file.');
        setUploadStatus('error');
        setSelectedFile(null);
        return;
      }

      setSelectedFile(file);
      setUploadStatus('idle');
      setErrorMessage('');
      setResult(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploadStatus('uploading');
    setErrorMessage('');

    try {
      // Call the API endpoint
      const data = await api.extractFromDocument(selectedFile);
      
      // Update state with success data
      setResult(data);
      setUploadStatus('success');
    } catch (error) {
      console.error('Upload failed:', error);
      setUploadStatus('error');
      setErrorMessage('Failed to extract document. Please check the file and try again.');
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-md border border-gray-200 overflow-hidden">
      <div className="p-6 border-b border-gray-100 bg-gray-50">
        <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2">
          <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path></svg>
          Upload Knowledge
        </h2>
        <p className="text-sm text-gray-500 mt-1">
          Upload PDF documents to index them into the knowledge base.
        </p>
      </div>

      <div className="p-6 space-y-6">
        {/* File Input Area */}
        <div className="flex items-center gap-4">
          <label className="block w-full">
            <span className="sr-only">Choose file</span>
            <input 
              type="file" 
              accept=".pdf"
              onChange={handleFileChange}
              disabled={uploadStatus === 'uploading'}
              className="block w-full text-sm text-slate-500
                file:mr-4 file:py-2.5 file:px-4
                file:rounded-full file:border-0
                file:text-sm file:font-semibold
                file:bg-indigo-50 file:text-indigo-700
                hover:file:bg-indigo-100
                cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed
              "
            />
          </label>
        </div>

        {/* Upload Action */}
        {selectedFile && uploadStatus !== 'success' && (
          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between text-sm text-gray-600 bg-gray-50 px-3 py-2 rounded">
              <span className="truncate max-w-[200px] font-medium">{selectedFile.name}</span>
              <span className="text-xs text-gray-400">
                {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
              </span>
            </div>
            
            <button
              onClick={handleUpload}
              disabled={uploadStatus === 'uploading'}
              className={`w-full py-2 px-4 rounded-lg font-medium text-white transition-all shadow-sm flex justify-center items-center gap-2
                ${uploadStatus === 'uploading' 
                  ? 'bg-indigo-400 cursor-wait' 
                  : 'bg-indigo-600 hover:bg-indigo-700 hover:shadow-md'
                }`}
            >
              {uploadStatus === 'uploading' ? (
                <>
                  <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Processing Document...
                </>
              ) : (
                'Start Extraction'
              )}
            </button>
          </div>
        )}

        {/* Error Message */}
        {uploadStatus === 'error' && (
          <div className="bg-red-50 border-l-4 border-red-500 text-red-700 p-4 rounded text-sm" role="alert">
            <p className="font-bold">Error</p>
            <p>{errorMessage}</p>
          </div>
        )}

        {/* Success / Result Display */}
        {uploadStatus === 'success' && result && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 animate-fade-in-up">
            <div className="flex items-center gap-2 mb-3">
              <div className="bg-green-100 p-1 rounded-full">
                <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path></svg>
              </div>
              <h3 className="font-semibold text-green-800">Extraction Complete</h3>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-white p-3 rounded border border-green-100 shadow-sm">
                <p className="text-xs text-gray-500 uppercase font-semibold">Content Length</p>
                <p className="text-2xl font-bold text-gray-800">{result.text_length.toLocaleString()}</p>
                <p className="text-xs text-gray-400">characters</p>
              </div>
              
              <div className="bg-white p-3 rounded border border-green-100 shadow-sm">
                <p className="text-xs text-gray-500 uppercase font-semibold">Images Found</p>
                <p className="text-2xl font-bold text-gray-800">{result.image_count}</p>
                <p className="text-xs text-gray-400">assets</p>
              </div>
            </div>
            
            <button 
              onClick={() => {
                setUploadStatus('idle');
                setSelectedFile(null);
                setResult(null);
              }}
              className="mt-4 text-sm text-green-700 hover:text-green-900 underline w-full text-center"
            >
              Upload another document
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default DocumentUpload;