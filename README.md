# AI Video Assistant with RAG

An AI-powered video analysis application that allows users to extract information from videos, generate summaries, and ask questions about video content using Retrieval-Augmented Generation (RAG).

The application converts video audio into text, processes the transcript, retrieves relevant information, and uses a Large Language Model (LLM) to generate context-aware answers.

## Features

* **YouTube Video Processing:** Extract audio from YouTube videos using `yt-dlp`.
* **Local Media Support:** Process supported local video and audio files.
* **Audio Processing:** Convert audio into a suitable format and divide it into manageable chunks using FFmpeg and Pydub.
* **Speech-to-Text Transcription:** Generate transcripts from audio using OpenAI Whisper.
* **Video Summarization:** Generate concise summaries of video content.
* **Retrieval-Augmented Generation (RAG):** Retrieve relevant transcript segments to answer user questions.
* **Semantic Search:** Find relevant information based on meaning rather than exact keyword matches.
* **Contextual Question Answering:** Ask questions about a video's content and receive answers grounded in its transcript.
* **Modular Architecture:** Separate components for audio processing, transcription, summarization, and retrieval.

## Tech Stack

| Technology            | Purpose                                   |
| --------------------- | ----------------------------------------- |
| Python                | Core application logic                    |
| OpenAI Whisper        | Audio transcription                       |
| LangChain             | LLM and RAG pipeline orchestration        |
| yt-dlp                | YouTube audio extraction                  |
| FFmpeg                | Audio conversion and processing           |
| Pydub                 | Audio manipulation and chunking           |
| Embedding Models      | Convert text into vector representations  |
| Vector Database       | Store and retrieve transcript embeddings  |
| Large Language Models | Generate summaries and contextual answers |
| Streamlit             | Web interface development                 |

*The exact embedding model, vector database, and LLM depend on the project's configuration.*

## How It Works

The application follows a video-to-knowledge pipeline.

1. **Input:** The user provides a YouTube URL or supported local media file.
2. **Audio Extraction:** Audio is extracted from the video using `yt-dlp` or the relevant media-processing utilities.
3. **Audio Processing:** FFmpeg and Pydub prepare the audio and divide it into manageable chunks.
4. **Transcription:** Whisper converts the audio into text.
5. **Text Processing:** The transcript is prepared for summarization and retrieval.
6. **Embedding Generation:** Transcript segments are converted into vector embeddings.
7. **Vector Storage:** The embeddings and associated text are stored in a vector database.
8. **Retrieval:** When the user asks a question, relevant transcript segments are retrieved.
9. **Answer Generation:** An LLM uses the retrieved context to generate a relevant answer.

### Architecture

```text
YouTube URL / Local Media
          |
          v
    Audio Extraction
          |
          v
 Audio Processing & Chunking
          |
          v
   Whisper Transcription
          |
          v
     Text Processing
          |
          +--------------------+
          |                    |
          v                    v
    Summarization       Embedding Generation
                               |
                               v
                        Vector Database
                               |
                         User Question
                               |
                               v
                         Retrieval
                               |
                               v
                       Retrieved Context
                               |
                               v
                         LLM Response
```

## Project Structure

```text
AI-Video-Assistant/
│
├── app.py
├── rag_engine.py
├── transcriber.py
├── summarize.py
├── vector_store.py
├── extractor.py
├── audio_processor.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

*Update this structure to match your actual repository. If these modules are inside folders such as `core/` or `utils/`, preserve their actual paths.*

## Installation and Setup

### Prerequisites

* Python 3.10 or a compatible version supported by your dependencies
* FFmpeg
* Git
* API credentials for the LLM or embedding provider used by your configuration

### 1. Clone the Repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd AI-Video-Assistant
```

Replace `<YOUR_GITHUB_REPOSITORY_URL>` with your repository's clone URL.

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install FFmpeg

Install FFmpeg and ensure it is available on your system's PATH.

Verify the installation:

```bash
ffmpeg -version
```

### 5. Configure Environment Variables

Create a `.env` file in the project root directory.

Add the environment variables required by your configuration. For example:

```env
OPENAI_API_KEY=your_api_key
```

Use the appropriate variable names for your selected providers.

**Security:** Never upload your actual `.env` file or API keys to GitHub. Use `.env.example` to document the required variables without exposing their values.

### 6. Run the Application

If your application uses Streamlit:

```bash
streamlit run app.py
```

If your current implementation uses a different entry point, run the appropriate Python module instead.

## Example Use Cases

* Summarize lengthy educational videos.
* Extract key concepts from technical tutorials.
* Ask questions about recorded lectures.
* Retrieve specific information from video transcripts.
* Build a searchable knowledge base from video content.
* Reduce the time required to review long-form video material.

## Future Improvements

* Improve transcription speed and processing efficiency.
* Add timestamp-aware answers linked to specific video segments.
* Support multiple videos within a single searchable knowledge base.
* Improve retrieval accuracy through chunking and reranking strategies.
* Add conversation history for follow-up questions.
* Develop a complete Streamlit interface for video uploads, summaries, transcripts, and question answering.

## Security

* Keep API keys and credentials in environment variables.
* Exclude `.env` and other sensitive files using `.gitignore`.
* Avoid committing private user data or confidential transcripts.
* Use `.env.example` to document required configuration variables.

## Author

**Shivansh Jha**

B.Tech Computer Science and Engineering — Data Science

---

*Built to explore video intelligence, speech recognition, Large Language Models, and Retrieval-Augmented Generation.*
