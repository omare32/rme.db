
// Home Page
// Slide bar
const myslide = document.querySelectorAll('.myslider');
const dot = document.querySelectorAll('.dot');

let counter = 1;
slideFun(counter);

let timer = setInterval(autoSlide, 8000);
function autoSlide() {
    counter += 1;
    slideFun(counter);
}

function plusSlides(n) {
    counter +=n;
    slideFun(counter);
    resetTimer();
}

function currentSlide(n) {
    counter = n;
    slideFun(counter);
    resetTimer();
}

function resetTimer() {
    clearInterval(timer);
    timer = setInterval(autoSlide, 8000);
}

function slideFun(n) {
    let i;
    for(i = 0; i < myslide.length; i++){
        myslide[i].style.display = 'none';
    }


    for(i = 0; i < dot.length; i++){
        dot[i].classList.remove('active');
    }

    if(n > myslide.length){
        counter = 1;
    }

    if(n < 1){
        counter = myslide.length;
    }
    myslide[counter - 1].style.display = 'block';
    dot[counter - 1].classList.add('active');

}

// End of Home Page

