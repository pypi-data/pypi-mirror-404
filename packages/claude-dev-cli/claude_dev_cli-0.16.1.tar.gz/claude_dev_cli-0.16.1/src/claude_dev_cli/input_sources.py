"""Input source handlers for reading specifications from various sources."""

from pathlib import Path
from typing import Optional, Tuple
from rich.console import Console


def read_text_input(text: str) -> str:
    """Read text input directly."""
    return text


def read_file_input(file_path: str) -> str:
    """Read input from a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File contents as string
        
    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file can't be read
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    return path.read_text(encoding='utf-8')


def read_pdf_input(pdf_path: str) -> str:
    """Read text content from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text from PDF
        
    Raises:
        ImportError: If pypdf is not installed
        FileNotFoundError: If PDF doesn't exist
        Exception: If PDF can't be parsed
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        raise ImportError(
            "PDF support requires pypdf. Install with: "
            "pip install 'claude-dev-cli[generation]'"
        )
    
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    
    try:
        reader = PdfReader(path)
        text_parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        
        if not text_parts:
            raise ValueError(f"No text could be extracted from PDF: {pdf_path}")
        
        return "\n\n".join(text_parts)
    except Exception as e:
        raise Exception(f"Failed to read PDF {pdf_path}: {str(e)}")


def read_url_input(url: str) -> str:
    """Fetch and extract text content from a URL.
    
    Args:
        url: URL to fetch
        
    Returns:
        Extracted text content
        
    Raises:
        ImportError: If requests or beautifulsoup4 are not installed
        Exception: If URL can't be fetched or parsed
    """
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        raise ImportError(
            "URL support requires requests and beautifulsoup4. Install with: "
            "pip install 'claude-dev-cli[generation]'"
        )
    
    # Validate URL format
    if not url.startswith(('http://', 'https://')):
        raise ValueError(f"Invalid URL format: {url}")
    
    try:
        # Fetch content
        response = requests.get(url, timeout=30, headers={
            'User-Agent': 'claude-dev-cli/0.11.0'
        })
        response.raise_for_status()
        
        # Determine content type
        content_type = response.headers.get('Content-Type', '').lower()
        
        if 'text/plain' in content_type:
            # Plain text - return as-is
            return response.text
        
        elif 'text/html' in content_type or 'application/xhtml' in content_type:
            # HTML - extract text
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(['script', 'style', 'nav', 'footer', 'header']):
                script.decompose()
            
            # Get text
            text = soup.get_text(separator='\n', strip=True)
            
            # Clean up extra whitespace
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            return '\n'.join(lines)
        
        elif 'application/json' in content_type:
            # JSON - return formatted
            import json
            return json.dumps(response.json(), indent=2)
        
        else:
            # Unknown content type - try to decode as text
            return response.text
    
    except requests.RequestException as e:
        raise Exception(f"Failed to fetch URL {url}: {str(e)}")
    except Exception as e:
        raise Exception(f"Failed to parse content from {url}: {str(e)}")


def get_input_content(
    description: Optional[str] = None,
    file_path: Optional[str] = None,
    pdf_path: Optional[str] = None,
    url: Optional[str] = None,
    console: Optional[Console] = None
) -> Tuple[str, str]:
    """Get input content from one of the available sources.
    
    Args:
        description: Direct text description
        file_path: Path to file
        pdf_path: Path to PDF
        url: URL to fetch
        console: Rich console for output
        
    Returns:
        Tuple of (content, source_description)
        
    Raises:
        ValueError: If multiple sources or no sources provided
        Various exceptions from individual read functions
    """
    if console is None:
        console = Console()
    
    # Count how many sources are provided
    sources = [
        ('description', description),
        ('file', file_path),
        ('pdf', pdf_path),
        ('url', url)
    ]
    provided_sources = [(name, value) for name, value in sources if value]
    
    if len(provided_sources) == 0:
        raise ValueError(
            "No input source provided. Use one of:\n"
            "  --description TEXT\n"
            "  -f/--file PATH\n"
            "  --pdf PATH\n"
            "  --url URL"
        )
    
    if len(provided_sources) > 1:
        source_names = [name for name, _ in provided_sources]
        raise ValueError(
            f"Multiple input sources provided: {', '.join(source_names)}. "
            f"Please use only one."
        )
    
    source_type, source_value = provided_sources[0]
    
    # Read from the appropriate source
    if source_type == 'description':
        content = read_text_input(source_value)
        source_desc = "text description"
    
    elif source_type == 'file':
        console.print(f"[cyan]Reading from file:[/cyan] {source_value}")
        content = read_file_input(source_value)
        source_desc = f"file: {source_value}"
    
    elif source_type == 'pdf':
        console.print(f"[cyan]Extracting text from PDF:[/cyan] {source_value}")
        try:
            content = read_pdf_input(source_value)
            console.print(f"[green]✓[/green] Extracted {len(content)} characters from PDF")
            source_desc = f"PDF: {source_value}"
        except ImportError as e:
            console.print(f"[red]Error:[/red] {str(e)}")
            raise
    
    elif source_type == 'url':
        console.print(f"[cyan]Fetching content from URL:[/cyan] {source_value}")
        try:
            content = read_url_input(source_value)
            console.print(f"[green]✓[/green] Fetched {len(content)} characters from URL")
            source_desc = f"URL: {source_value}"
        except ImportError as e:
            console.print(f"[red]Error:[/red] {str(e)}")
            raise
    
    else:
        raise ValueError(f"Unknown source type: {source_type}")
    
    return content, source_desc
