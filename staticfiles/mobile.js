
function toggleCustomSidebar() {
    const sidebar = document.getElementById('custom-sidebar');
    if (sidebar.style.display === 'none' || sidebar.style.display === '') {
        sidebar.style.display = 'block';
        document.addEventListener('click', handleOutsideClick);
    } else {
        sidebar.style.display = 'none';
        document.removeEventListener('click', handleOutsideClick);
    }
}

function handleOutsideClick(event) {
    const sidebar = document.getElementById('custom-sidebar');
    const toggleButton = document.querySelector('.custom-sidebar-toggle');
    if (!sidebar.contains(event.target) && !toggleButton.contains(event.target)) {
        sidebar.style.display = 'none';
        document.removeEventListener('click', handleOutsideClick);
    }
}

function toggleApp(appName) {
    const appSection = document.getElementById(`app-${appName}`);
    if (appSection.style.display === 'block' || appSection.style.display === '') {
        appSection.style.display = 'none';
    } else {
        appSection.style.display = 'block';
    }
}
document.addEventListener("DOMContentLoaded", function() {
    window.toggleRentalDays = function(id) {
        const rentalSection = document.getElementById(id);
        rentalSection.classList.toggle("hidden");
    };
});