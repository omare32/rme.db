// import sectors from '/data/sectors.json' assert {type: 'json'};
const sectors = ['Health and Social Care',
'Pharmaceutical',
'Life Science',
'Industrial and Manufacturing',
'Farming and Agriculture',
'Food and Beverage',
'Creative Industries',
'Energy Sector',
'Transport and Logistics',
'Education',
'Automotive'];


// dropdown list
// Select Box
const sectorInput = document.querySelector('#sector');

const selectedAll = document.querySelectorAll('.selected');

selectedAll.forEach(selected => {
    const optionsContainer = selected.previousElementSibling;
    const searchBox = selected.nextElementSibling;

    const optionList = optionsContainer.querySelectorAll('.option');
    // if ( a == h){
    //     selected.querySelector('#sector').value = 'Health and Social Care'
    // }

    selected.addEventListener('click', () => {

        if(optionsContainer.classList.contains('active-box')){
            optionsContainer.classList.remove('active-box');
        } else {
            let currentActive = document.querySelector('.options-container.active-box');

            if(currentActive){
                currentActive.classList.remove('active-box')
            }

            optionsContainer.classList.add('active-box')
        }
        // optionsContainer.classList.toggle('active-box');

        searchBox.value = '';
        filterlist('');

        if(optionsContainer.classList.contains('active-box')) {
            searchBox.focus();
        }
    });

    optionList.forEach(o => {
        o.addEventListener('click', () => {
            // selected.innerHTML = o.querySelector('label').innerHTML;
            selected.querySelector('#sector').value = o.querySelector('label').innerHTML;

            optionsContainer.classList.remove('active-box')
        });
    });

    // Search Box
    searchBox.addEventListener('keyup', function(e) {
        filterlist(e.target.value);
    });

    const filterlist = searchTerm => {
        searchTerm = searchTerm.toLowerCase();
        optionList.forEach(option => {
            let label = option.firstElementChild.nextElementSibling.innerText.toLowerCase();
            if(label.indexOf(searchTerm) != -1) {
                option.style.display = 'block';  
            } else{
                option.style.display = 'none'
            }
        });
    }

});


sectorInput.addEventListener('change', () => {
    sectors.forEach(sect => {
        if (sect !== sectorInput.value) {
            sectorInput.value = '';
        }
    })
    if (sectorInput.value === '') {
        alert('Please choose from the available sectors list.');
    }
})


// End Select Box

