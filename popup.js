document.addEventListener('DOMContentLoaded', function() {
  const button = document.getElementById('readMessages');
  const messageCountInput = document.getElementById('messageCount');
  const status = document.getElementById('status');

  // Load saved message count
  chrome.storage.local.get(['messageCount'], function(result) {
    if (result.messageCount) {
      messageCountInput.value = result.messageCount;
    }
  });

  // Save message count when changed
  messageCountInput.addEventListener('change', function() {
    chrome.storage.local.set({ messageCount: messageCountInput.value });
  });

  button.addEventListener('click', async function() {
    const count = parseInt(messageCountInput.value);
    
    if (count < 1 || count > 50) {
      status.textContent = 'Please enter a number between 1 and 50';
      status.className = 'error';
      return;
    }

    status.textContent = 'Starting message reader...';
    
    try {
      const response = await fetch(`http://localhost:8000/read_messages/${count}`);
      const data = await response.json();
      
      if (response.ok) {
        status.textContent = data.message;
        status.className = 'success';
      } else {
        status.textContent = `Error: ${data.detail}`;
        status.className = 'error';
      }
    } catch (error) {
      status.textContent = `Error: ${error.message}. Make sure the server is running.`;
      status.className = 'error';
    }
  });
}); 