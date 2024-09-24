// Navigation Bar

const Nav = document.querySelector(".navigation");
const navToggle = document.querySelector(".mobile-nav-toggle");

navToggle.addEventListener("click", () => {
    const visibility = Nav.getAttribute("data-visible");

    if(visibility === "false") {
        Nav.setAttribute("data-visible", true);
        navToggle.setAttribute("aria-expand", true)
    } else if(visibility === "true") {
        Nav.setAttribute("data-visible", false);
        navToggle.setAttribute("aria-expand", false)
    }
})

// End of Navigation Bar