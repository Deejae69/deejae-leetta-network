document.getElementById('signupForm').addEventListener('submit', function (event) {
  event.preventDefault();

  const name = document.getElementById('name').value.trim();
  const email = document.getElementById('email').value.trim();
  const role = document.getElementById('role').value.trim();
  const message = document.getElementById('message');

  if (!name || !email || !role) {
    message.textContent = 'Please fill in all fields.';
    return;
  }

  message.textContent = `Welcome, ${name}! Your account request for ${role} has been created.`;
  event.target.reset();
});
