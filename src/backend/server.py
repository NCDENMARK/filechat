from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import os

# Import our custom modules
from pdf_processor import PDFProcessor
from word_processor import WordProcessor
from pp_processor import PPProcessor
from excel_processor import ExcelProcessor
from vector_store import VectorStore
from chat_engine import ChatEngine
from config import CHUNK_SIZE, CHUNK_OVERLAP

# Create FastAPI application
app = FastAPI()

# Allow the Electron frontend to talk to this server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Accept requests from any origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],
)

# Create instances of our classes - chat_engine uses shared vector_store
pdf_processor = PDFProcessor()
word_processor = WordProcessor()
pp_processor = PPProcessor()
excel_processor = ExcelProcessor()
vector_store = VectorStore()
chat_engine = ChatEngine(vector_store)  # Pass the shared instance

# Define what the incoming requests should look like
class IndexRequest(BaseModel):
    folder_path: str  # Path to folder containing PDFs, Word docs, PowerPoints, and Excel files

class ChatRequest(BaseModel):
    question: str  # User's question
    folder_path: Optional[str] = None  # Optional: filter to specific folder

# Health check endpoint - test if server is running
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Endpoint to get list of all indexed folders
@app.get("/folders")
async def get_folders():
    """Get list of all folders that have been indexed"""
    try:
        folders = vector_store.get_indexed_folders()
        return {"status": "success", "folders": folders}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to clear the database
@app.post("/clear")
async def clear_database():
    """Clear all indexed documents from the vector store"""
    try:
        success = vector_store.clear_collection()
        if success:
            return {"status": "success", "message": "Database cleared"}
        else:
            return {"status": "error", "message": "Failed to clear database"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to index PDFs, Word documents, PowerPoint presentations, and Excel files in a folder
@app.post("/index")
async def index_folder(request: IndexRequest):
    """Process all PDFs, Word documents, PowerPoints, and Excel files in the specified folder"""
    try:
        # Step 1: Find all PDFs, Word documents, PowerPoints, and Excel files in the folder
        pdf_files = pdf_processor.scan_directory(request.folder_path)
        word_files = word_processor.scan_directory(request.folder_path)
        pp_files = pp_processor.scan_directory(request.folder_path)
        excel_files = excel_processor.scan_directory(request.folder_path)
        
        if not pdf_files and not word_files and not pp_files and not excel_files:
            return {"status": "no_files", "message": "No PDF, Word, PowerPoint, or Excel files found in the directory"}
        
        indexed_pdf_files = []  # Track successfully processed PDFs
        indexed_word_files = []  # Track successfully processed Word docs
        indexed_pp_files = []  # Track successfully processed PowerPoints
        indexed_excel_files = []  # Track successfully processed Excel files
        
        # Step 2: Process each PDF
        for pdf_path in pdf_files:
            # Extract all text from the PDF
            pdf_data = pdf_processor.extract_text(pdf_path)
            
            if pdf_data["status"] == "success":
                # Break text into smaller chunks
                chunks = pdf_processor.split_into_chunks(
                    pdf_data["text"], 
                    CHUNK_SIZE,  # 500 words per chunk
                    CHUNK_OVERLAP  # 50 word overlap
                )
                
                # Store chunks in vector database with folder information
                vector_store.add_documents(
                    chunks,
                    {
                        "file_name": pdf_data["file_name"],
                        "file_path": pdf_data["file_path"],
                        "file_type": "PDF",
                        "folder_path": request.folder_path
                    },
                    pdf_data["file_id"]
                )
                
                indexed_pdf_files.append(pdf_data["file_name"])
        
        # Step 3: Process each Word document
        for word_path in word_files:
            # Extract all text from the Word document
            word_data = word_processor.extract_text(word_path)
            
            if word_data["status"] == "success":
                # Break text into smaller chunks
                chunks = word_processor.split_into_chunks(
                    word_data["text"],
                    CHUNK_SIZE,  # 500 words per chunk
                    CHUNK_OVERLAP  # 50 word overlap
                )
                
                # Store chunks in vector database with folder information
                vector_store.add_documents(
                    chunks,
                    {
                        "file_name": word_data["file_name"],
                        "file_path": word_data["file_path"],
                        "file_type": "Word",
                        "folder_path": request.folder_path
                    },
                    word_data["file_id"]
                )
                
                indexed_word_files.append(word_data["file_name"])
        
        # Step 4: Process each PowerPoint presentation
        for pp_path in pp_files:
            # Extract all text from the PowerPoint
            pp_data = pp_processor.extract_text(pp_path)
            
            if pp_data["status"] == "success":
                # Break text into smaller chunks
                chunks = pp_processor.split_into_chunks(
                    pp_data["text"],
                    CHUNK_SIZE,  # 500 words per chunk
                    CHUNK_OVERLAP  # 50 word overlap
                )
                
                # Store chunks in vector database with folder information
                vector_store.add_documents(
                    chunks,
                    {
                        "file_name": pp_data["file_name"],
                        "file_path": pp_data["file_path"],
                        "file_type": "PowerPoint",
                        "folder_path": request.folder_path
                    },
                    pp_data["file_id"]
                )
                
                indexed_pp_files.append(pp_data["file_name"])
        
        # Step 5: Process each Excel file
        for excel_path in excel_files:
            # Extract all data from the Excel file
            excel_data = excel_processor.extract_text(excel_path)
            
            if excel_data["status"] == "success":
                # Break text into smaller chunks
                chunks = excel_processor.split_into_chunks(
                    excel_data["text"],
                    CHUNK_SIZE,  # 500 words per chunk
                    CHUNK_OVERLAP  # 50 word overlap
                )
                
                # Store chunks in vector database with folder information
                vector_store.add_documents(
                    chunks,
                    {
                        "file_name": excel_data["file_name"],
                        "file_path": excel_data["file_path"],
                        "file_type": "Excel",
                        "folder_path": request.folder_path
                    },
                    excel_data["file_id"]
                )
                
                indexed_excel_files.append(excel_data["file_name"])
        
        # Combine all indexed files
        all_indexed_files = indexed_pdf_files + indexed_word_files + indexed_pp_files + indexed_excel_files
        
        # Return summary of what was indexed
        return {
            "status": "success",
            "indexed_files": all_indexed_files,
            "total_files": len(all_indexed_files),
            "pdf_count": len(indexed_pdf_files),
            "word_count": len(indexed_word_files),
            "pp_count": len(indexed_pp_files),
            "excel_count": len(indexed_excel_files),
            "folder_path": request.folder_path
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to answer questions
@app.post("/chat")
async def chat(request: ChatRequest):
    """Answer a question using the indexed documents"""
    try:
        response = chat_engine.ask_question(request.question, request.folder_path)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Start the server when this file is run directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)  # Run on localhost:8000