const log = document.getElementById('log');
const sendBtn = document.getElementById('sendBtn');

function appendMessage(role, text, meta) {
  const container = document.createElement('div');
  container.className = `msg ${role}`;

  const body = document.createElement('div');
  body.textContent = text;

  container.appendChild(body);

  if (meta) {
    const metaNode = document.createElement('div');
    metaNode.className = 'meta';
    metaNode.textContent = meta;
    container.appendChild(metaNode);
  }

  log.prepend(container);
}

async function sendMessage() {
  const employeeId = document.getElementById('employeeId').value.trim();
  const message = document.getElementById('message').value.trim();

  if (!employeeId || !message) {
    return;
  }

  appendMessage('user', message, `employee=${employeeId}`);

  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ employee_id: employeeId, message }),
  });

  const payload = await response.json();
  appendMessage('bot', payload.message, `route=${payload.route}; status=${payload.status}`);

  document.getElementById('message').value = '';
}

sendBtn.addEventListener('click', () => {
  sendMessage().catch((error) => {
    appendMessage('bot', 'Failed to contact service.', String(error));
  });
});
