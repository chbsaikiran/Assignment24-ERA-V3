document.addEventListener('DOMContentLoaded', function() {
  const processButton = document.getElementById('processButton');
  const queryInput = document.getElementById('queryInput');
  const statusDiv = document.getElementById('status');

  processButton.addEventListener('click', async function() {
    const query = queryInput.value.trim();
    
    if (!query) {
      showStatus('Please enter a query', false);
      return;
    }

    try {
      processButton.disabled = true;
      processButton.textContent = 'Processing...';
      
      const response = await fetch('http://127.0.0.1:8000/process_query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          query: query
        })
      });

      const data = await response.json();

      if (response.ok) {
        showStatus('Query processed successfully!', true);
      } else {
        let errorMessage = 'An error occurred';
        if (data.detail) {
          errorMessage = typeof data.detail === 'object' 
            ? JSON.stringify(data.detail) 
            : data.detail;
        }
        showStatus(`Error: ${errorMessage}`, false);
        console.error('Server response:', data);
      }
    } catch (error) {
      console.error('Error details:', error);
      showStatus('Error connecting to server. Please make sure the server is running.', false);
    } finally {
      processButton.disabled = false;
      processButton.textContent = 'Process Query';
    }
  });

  function showStatus(message, isSuccess) {
    statusDiv.textContent = message;
    statusDiv.style.display = 'block';
    statusDiv.className = isSuccess ? 'success' : 'error';
    
    // Hide status after 5 seconds
    setTimeout(() => {
      statusDiv.style.display = 'none';
    }, 5000);
  }
}); 