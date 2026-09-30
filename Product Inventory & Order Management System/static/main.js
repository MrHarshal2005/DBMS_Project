document.addEventListener("DOMContentLoaded", function () {
  // Quantity steppers (used on product detail & cart pages)
  document.querySelectorAll("[data-qty-stepper]").forEach(function (wrapper) {
    const input = wrapper.querySelector("input[type=number]");
    const max = parseInt(input.getAttribute("max") || "9999", 10);
    const min = parseInt(input.getAttribute("min") || "1", 10);

    wrapper.querySelectorAll("[data-qty-action]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        let value = parseInt(input.value || min, 10);
        if (btn.dataset.qtyAction === "increase") value = Math.min(max, value + 1);
        if (btn.dataset.qtyAction === "decrease") value = Math.max(min, value - 1);
        input.value = value;
      });
    });
  });

  // Confirm before destructive actions
  document.querySelectorAll("[data-confirm]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      if (!confirm(form.dataset.confirm)) {
        e.preventDefault();
      }
    });
  });

  // Auto-dismiss alerts after 5 seconds
  document.querySelectorAll(".alert").forEach(function (alertEl) {
    setTimeout(function () {
      const alert = bootstrap.Alert.getOrCreateInstance(alertEl);
      alert.close();
    }, 5000);
  });
});
