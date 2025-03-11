
// LogIn-alert box javascript
function showMessage(message, type) {
    let alertBox = document.getElementById("alertBox");
    alertBox.textContent = message;
    alertBox.className = "alert " + type;
    alertBox.style.display = "block";

    setTimeout(() => { alertBox.style.display = "none"; }, 3000);
}

// window.onload = function () {
//     {% with messages = get_flashed_messages(with_categories = True) %}
//     {% if messages %}
//     {% for category, message in messages %}
//     showMessage("{{ message }}", "{{ category }}");
//     {% endfor %}
//     {% endif %}
//     {% endwith %}
// };


document.addEventListener('DOMContentLoaded', function () {
    // Handle password visibility toggle
    const togglePassword = document.querySelector('.toggle-password');
    const passwordInput = document.querySelector('input[name="password"]');

    togglePassword?.addEventListener('click', function () {
        const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
        passwordInput.setAttribute('type', type);
        this.innerHTML = type === 'password' ? '<i class="far fa-eye"></i>' : '<i class="far fa-eye-slash"></i>';
    });
});

document.addEventListener('DOMContentLoaded', function () {
    let profileBtn = document.getElementById('profileBtn');
    let profileDropdown = document.getElementById('profileDropdown');

    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener("click", function (event) {
            event.preventDefault(); // Prevent default jump behavior

            const target = document.querySelector(this.getAttribute("href"));
            if (target) {
                window.scrollTo({
                    top: target.offsetTop - 50, // Adjust for navbar height if needed
                    behavior: "smooth"
                });
            }
        });
    });

//     profileBtn.addEventListener('click', function (event) {
//         event.stopPropagation(); // Prevent dropdown from closing immediately when clicking the icon
//         if (profileDropdown.style.display === "none" || profileDropdown.style.display === "") {
//             profileDropdown.style.display = "block";
//         } else {
//             profileDropdown.style.display = "none";
//         }
//     });

//     // Close dropdown when clicking outside
//     document.addEventListener('click', function (event) {
//         if (!profileDropdown.contains(event.target) && !profileBtn.contains(event.target)) {
//             profileDropdown.style.display = "none";
//         }
//     });
});

