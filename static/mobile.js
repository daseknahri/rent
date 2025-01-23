
function toggleCustomSidebar() {
    const sidebar = document.getElementById('custom-sidebar');
    if (sidebar) {
        if (sidebar.style.display === 'block') {
            sidebar.style.display = 'none'; // Hide the sidebar
        } else {
            sidebar.style.display = 'block'; // Show the sidebar
        }
    }
}