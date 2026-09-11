document.addEventListener('DOMContentLoaded', function () {
  // Global form handler for all forms with class "swal-ajax-form"
  document.body.addEventListener('submit', function (e) {
    const form = e.target.closest('.swal-ajax-form');
    if (!form) return; // Not our form

    e.preventDefault();

    const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]')?.value;
    const formAction = form.action;

    // 🔒 Disable submit button to prevent double-click
    const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
    if (submitBtn) submitBtn.disabled = true;

    Swal.fire({
      title: 'Processing...',
      text: 'Please wait while we process your request.',
      allowOutsideClick: false,
      didOpen: () => {
        Swal.showLoading();
      }
    });

    fetch(formAction, {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrfToken,
        'Accept': 'application/json'
      }
    })
    .then(res => res.json())
    .then(data => {
      Swal.close();
      Swal.fire({
        icon: data.status === 'success' ? 'success' : 'error',
        title: data.status === 'success' ? 'Success' : 'Failed',
        text: data.message || 'Something happened.'
      });
    })
    .catch(err => {
      Swal.close();
      Swal.fire({
        icon: 'error',
        title: 'Network Error',
        text: 'Please try again.'
      });
    })
    .finally(() => {
      if (submitBtn) submitBtn.disabled = false;
    });
  });
});
