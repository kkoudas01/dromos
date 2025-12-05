const subjects = {
  'Άλγεβρα': ['Εξισώσεις', 'Ανισώσεις'],
  'Γεωμετρία': ['Σχήματα', 'Γωνίες','Τριγωνομετρία'],
  'Φυσική': ['Κινηματική', 'Δυναμική']
};

const links = {
  'Εξισώσεις': [
    { text: 'Γραμμικές Εξισώσεις', url: 'ex1.html' },
    { text: 'Δευτεροβάθμιες Εξισώσεις', url: 'ex2.html' }
  ],
  'Ανισώσεις': [
    { text: 'Γραμμικές Ανισώσεις', url: 'an1.html' }
  ],
  'Σχήματα': [
    { text: 'Τρίγωνα', url: 'sx1.html' },
    { text: 'Τετράπλευρα', url: 'sx2.html' }
  ],
  'Τριγωνομετρία': [
    { text: 'Τριγωνομετρικοί αριθμοί κυρτών γωνιών', url: 'trigonArithGgymn.html' },
    { text: 'Τετράπλευρα', url: 'sx2.html' }
  ],
  'Γωνίες': [
    { text: 'Είδη Γωνιών', url: 'gn1.html' },
    { text: 'Υπολογισμοί', url: 'gn2.html' }
  ],
  'Κινηματική': [
    { text: 'Ομαλή Κίνηση', url: 'kin1.html' },
    { text: 'Ευθύγραμμη Κίνηση', url: 'kin2.html' }
  ],
  'Δυναμική': [
    { text: 'Νόμοι του Νεύτωνα', url: 'dyn1.html' },
    { text: 'Δυνάμεις', url: 'dyn2.html' }
  ]
};

const ringButtons = document.querySelectorAll('.ring-button');
const centralCircle = document.getElementById('main-label');
const dropdownsContainer = document.getElementById('dropdowns');
const backButton = document.querySelector('.back-button');

let currentlySelectedButton = null;
let animationInProgress = false;

function getInitialTransform(button) {
  const index = Array.from(ringButtons).indexOf(button);
  switch(index) {
    case 0: return 'translate(160px, 0)';
    case 1: return 'rotate(120deg) translate(160px) rotate(-120deg)';
    case 2: return 'rotate(240deg) translate(160px) rotate(-240deg)';
    default: return '';
  }
}

function resetButtonToInitialPosition(button, callback) {
  if (!button) return;
  
  button.classList.remove('selected');
  button.style.transform = getInitialTransform(button);
  button.style.opacity = '1';
  button.style.pointerEvents = 'auto';
  
  if (callback) callback();
}

function moveButtonToCenter(button, callback) {
  if (!button) return;
  
  button.classList.add('selected');
  
  setTimeout(() => {
    button.style.transform = 'scale(0.5) translate(0, 0)';
    button.style.opacity = '0';
    button.style.pointerEvents = 'none';
    
    if (callback) setTimeout(callback, 500);
  }, 10);
}

function selectButton(button) {
  if (animationInProgress) return;
  animationInProgress = true;
  
  const subject = button.dataset.subject;
  
  if (currentlySelectedButton && currentlySelectedButton !== button) {
    resetButtonToInitialPosition(currentlySelectedButton, () => {
      moveButtonToCenter(button, () => {
        currentlySelectedButton = button;
        centralCircle.innerText = subject;
        centralCircle.classList.add('can-reset');
        createDropdownMenu(subject);
        animationInProgress = false;
      });
    });
  } else {
    moveButtonToCenter(button, () => {
      currentlySelectedButton = button;
      centralCircle.innerText = subject;
      centralCircle.classList.add('can-reset');
      createDropdownMenu(subject);
      animationInProgress = false;
    });
  }
}

function resetToDefaultState() {
  if (animationInProgress || !currentlySelectedButton) return;
  animationInProgress = true;
  
  resetButtonToInitialPosition(currentlySelectedButton, () => {
    currentlySelectedButton = null;
    centralCircle.innerText = 'Γ Γυμνασίου';
    centralCircle.classList.remove('can-reset');
    dropdownsContainer.innerHTML = '';
    animationInProgress = false;
  });
  
  centralCircle.style.transform = 'scale(0.9)';
  setTimeout(() => {
    centralCircle.style.transform = '';
  }, 300);
}

ringButtons.forEach(button => {
  button.addEventListener('click', (e) => {
    e.stopPropagation();
    if (button !== currentlySelectedButton) {
      selectButton(button);
    }
  });
});

centralCircle.addEventListener('click', (e) => {
  e.stopPropagation();
  if (currentlySelectedButton) {
    resetToDefaultState();
  }
});

backButton.addEventListener('click', (e) => {
  e.stopPropagation();
  
  // 1. Επαναφορά της τρέχουσας κατάστασης (αν υπάρχει επιλεγμένο κουμπί)
  if (currentlySelectedButton) {
    resetToDefaultState();
    
    // 2. Μεταφόρτωση της αρχικής σελίδας με μικρή καθυστέρηση
    setTimeout(() => {
      window.location.href = '../index.html';
    }, 500); // Περιμένετε να ολοκληρωθεί το animation της επαναφοράς
  } else {
    // Αν δεν υπάρχει τίποτα επιλεγμένο, πηγαίνετε απευθείας στην αρχική
    window.location.href = '../index.html';
  }
});

document.querySelector('.ring').addEventListener('click', (e) => {
  e.stopPropagation();
});

function createDropdownMenu(subject) {
  dropdownsContainer.innerHTML = '';
  
  const container = document.createElement('div');
  container.className = 'dropdown-container';
  
  const dropdown = document.createElement('div');
  dropdown.className = 'dropdown';
  
  subjects[subject].forEach(topic => {
    const topicButton = document.createElement('button');
    topicButton.innerText = topic;
    topicButton.dataset.topic = topic;
    
    topicButton.addEventListener('click', (e) => {
      e.stopPropagation();
      document.querySelectorAll('.submenu').forEach(menu => menu.remove());
      createSubmenu(e.target, topic);
      
      e.target.style.transform = 'translateX(5px)';
      setTimeout(() => { e.target.style.transform = ''; }, 200);
    });
    
    dropdown.appendChild(topicButton);
  });
  
  container.appendChild(dropdown);
  dropdownsContainer.appendChild(container);
  
  dropdownsContainer.style.opacity = '0';
  dropdownsContainer.style.transform = 'translateY(-10px)';
  setTimeout(() => {
    dropdownsContainer.style.opacity = '1';
    dropdownsContainer.style.transform = 'translateY(0)';
  }, 10);
}

function createSubmenu(parentButton, topic) {
  const submenu = document.createElement('div');
  submenu.className = 'submenu';
  
  links[topic].forEach(link => {
    const linkButton = document.createElement('button');
    linkButton.innerText = link.text;
    linkButton.addEventListener('click', (e) => {
      e.stopPropagation();
      window.location.href = link.url;
    });
    
    linkButton.addEventListener('mouseenter', () => { 
      linkButton.style.transform = 'translateX(3px)'; 
    });
    linkButton.addEventListener('mouseleave', () => { 
      linkButton.style.transform = ''; 
    });
    
    submenu.appendChild(linkButton);
  });

  const dropdownContainer = parentButton.closest('.dropdown-container');
  
  submenu.style.position = 'absolute';
  submenu.style.left = '100%';
  submenu.style.top = '0';
  submenu.style.marginLeft = '10px';
  
  dropdownContainer.appendChild(submenu);
  
  submenu.style.opacity = '0';
  submenu.style.transform = 'translateX(-10px)';
  setTimeout(() => {
    submenu.style.opacity = '1';
    submenu.style.transform = 'translateX(0)';
  }, 10);
}