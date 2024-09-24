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

const mobileInput = document.querySelector('#mobile');
// dropdown list
// Select Box

const sectorInput = document.querySelector('#sector');
// sectorInput.setAttribute('readonly', 'true')

const timePatternInput = document.querySelector('.time-pattern');
// timePatternInput.setAttribute('readonly', 'true')


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
});

timePatternInput.addEventListener('change', () => {
    if (timePatternInput.value !== 'Full-time' ||  timePatternInput.value !== 'Part-time') {
        timePatternInput.value = '';
    alert('Please choose from the available time patterns.');
    }
});


// End Select Box

// Mobile no.
var input = document.querySelector("#phone");


var input = document.querySelector("#phone"),
  errorMsg = document.querySelector("#error-msg"),
  validMsg = document.querySelector("#valid-msg");

// here, the index maps to the error code returned from getValidationError - see readme
var errorMap = ["Invalid number", "Invalid country code", "Too short", "Too long", "Invalid number"];

// initialise plugin
var iti = window.intlTelInput(input, {
    initialCountry: "auto",
    geoIpLookup: getIp,
    utilsScript: "../../js/forms/utils.js?1638200991544"
});

var reset = function() {
  input.classList.remove("error");
  errorMsg.innerHTML = "";
  errorMsg.classList.add("hide");
  validMsg.classList.add("hide");
};

// on blur: validate
input.addEventListener('blur', function() {
  reset();
  if (input.value.trim()) {
    if (iti.isValidNumber()) {
      validMsg.classList.remove("hide");
    } else {
      input.classList.add("error");
      var errorCode = iti.getValidationError();
      errorMsg.innerHTML = errorMap[errorCode];
      errorMsg.classList.remove("hide");
    }
  }
});

// on keyup / change flag: reset
input.addEventListener('change', reset);
input.addEventListener('keyup', reset);

function getIp(callback) {
    fetch('https://ipinfo.io/json?token=3445c2e98ce299', { headers: { 'Accept': 'application/json' }})
      .then((resp) => resp.json())
      .catch(() => {
        return {
          country: 'us',
        };
      })
      .then((resp) => callback(resp.country));
}

function process(event) {
 event.preventDefault();

 const phoneNumber = iti.getNumber();

 mobileInput.value = phoneNumber;
}

input.addEventListener('change', event => {
    process(event);
})



