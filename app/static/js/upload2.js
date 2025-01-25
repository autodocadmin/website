let fileGroupCount = 0;

function addFileInput() {
    // Check if files are selected in the current set before adding a new one
    if (fileGroupCount > 0 && !areFilesSelected()) {
        alert("Please select at least one file in the current set before adding a new one.");
        return false;
    }

    fileGroupCount++;
    document.getElementById('fileGroupCountInput').value = fileGroupCount;
    const fileList = document.getElementById('fileList');
    const fileInputWrapper = document.createElement('div');
    fileInputWrapper.classList.add('file-input-wrapper');
    fileInputWrapper.id = `file-group-${fileGroupCount}`;

    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.name = `fileInput[]`;
    fileInput.multiple = true;
    
    fileInput.onchange = function() { displayUploadedFiles(this); };

    // Automatically trigger file dialog for sets beyond the first
    if (fileGroupCount > 1) {
        fileInput.style.display = 'none';
        setTimeout(() => fileInput.click(), 0);
    }
    
    fileInputWrapper.appendChild(fileInput);

    const fileDisplayArea = document.createElement('div');
    fileDisplayArea.id = `file-display-${fileGroupCount}`;
    fileDisplayArea.classList.add('file-display-area');
    fileInputWrapper.appendChild(fileDisplayArea);

    fileList.appendChild(fileInputWrapper);

    // Remove any existing "Add More Files" button
    const existingButton = document.querySelector('.add-file-btn');
    if (existingButton) {
        existingButton.remove();
    }

    // Add "Add More Files" button after the new file input
    const addButton = document.createElement('button');
    addButton.textContent = 'Add More Files';
    addButton.classList.add('add-file-btn');
    addButton.onclick = addFileInput;
    fileList.appendChild(addButton);
}

function displayUploadedFiles(input) {
    const fileDisplayArea = document.getElementById(`file-display-${fileGroupCount}`);
    fileDisplayArea.innerHTML = ''; 

    if (input.files.length > 0) {
        const fileTable = document.createElement('table');
        fileTable.classList.add('file-table');

        for (let i = 0; i < input.files.length; i++) {
            const fileBlock = document.createElement('tbody');
            fileBlock.classList.add('file-block');

            // File name row
            const fileNameRow = document.createElement('tr');
            const fileNameCell = document.createElement('td');
            fileNameCell.colSpan = 7;
            fileNameCell.textContent = input.files[i].name;
            fileNameCell.classList.add('file-name');
            fileNameRow.appendChild(fileNameCell);
            fileBlock.appendChild(fileNameRow);

            // Properties row
            const fileRow = document.createElement('tr');
            fileRow.classList.add('file-row');

            // Copies selection
            const counterWrapper = createCounter(i);
            fileRow.appendChild(counterWrapper);

            // Orientation selection
            const orientationWrapper = createOrientationSelector(fileGroupCount, i);
            fileRow.appendChild(orientationWrapper);


            // Color selection
            const colorWrapper = createColorSelector(fileGroupCount, i);
            fileRow.appendChild(colorWrapper);

            // Side selection
            const sideWrapper = createSideSelector(fileGroupCount, i);
            fileRow.appendChild(sideWrapper);

            // Page range selection
            const pageRangeWrapper = createPageRangeSelector(i);
            fileRow.appendChild(pageRangeWrapper);

            fileBlock.appendChild(fileRow);
            fileTable.appendChild(fileBlock);
        }

        fileDisplayArea.appendChild(fileTable);
    }

    // Hide the file input after files are selected
    input.style.display = 'none';
}

// Helper function to create the counter selector
function createCounter(index) {
    const counterWrapper = document.createElement('td');
    counterWrapper.classList.add('counter-wrapper');

    const noofcopiesLabel = document.createElement('span');
    noofcopiesLabel.textContent = "Choose Number of Copies";
    
    const minusButton = document.createElement('button');
    minusButton.type = 'button';
    minusButton.textContent = '-';
    minusButton.onclick = function() { updateCounter(this, 'minus'); };

    const counterInput = document.createElement('input');
    counterInput.type = 'text';
    counterInput.classList.add('counter');
    counterInput.value = '1';
    counterInput.name = `copies[]`;
    counterInput.oninput = function() { validateCounter(this); };

    const plusButton = document.createElement('button');
    plusButton.type = 'button';
    plusButton.textContent = '+';
    plusButton.onclick = function() { updateCounter(this, 'plus'); };

    counterWrapper.appendChild(noofcopiesLabel);
    counterWrapper.appendChild(minusButton);
    counterWrapper.appendChild(counterInput);
    counterWrapper.appendChild(plusButton);

    return counterWrapper;
}

// Helper function to create the orientation selector
function createOrientationSelector(groupIndex, fileIndex) {
    const orientationWrapper = document.createElement('td');
    orientationWrapper.classList.add('orientation-wrapper');

    const orientationTitle = document.createElement('div');
    orientationTitle.textContent = "Choose Print Orientation";

    const portraitLabel = document.createElement('label');
    const portraitInput = document.createElement('input');
    portraitInput.type = 'radio';
    portraitInput.name = `orientation[${groupIndex}][${fileIndex}]`;
    portraitInput.value = 'portrait';
    portraitInput.checked = true;
    portraitLabel.appendChild(portraitInput);
    portraitLabel.appendChild(document.createTextNode('Portrait'));

    const landscapeLabel = document.createElement('label');
    const landscapeInput = document.createElement('input');
    landscapeInput.type = 'radio';
    landscapeInput.name = `orientation[${groupIndex}][${fileIndex}]`;
    landscapeInput.value = 'landscape';
    landscapeLabel.appendChild(landscapeInput);
    landscapeLabel.appendChild(document.createTextNode('Landscape'));

    orientationWrapper.appendChild(orientationTitle);
    orientationWrapper.appendChild(portraitLabel);
    orientationWrapper.appendChild(landscapeLabel);

    return orientationWrapper;
}

// Helper function to create the color selector
function createColorSelector(groupIndex, fileIndex) {
    const colorWrapper = document.createElement('td');
    colorWrapper.classList.add('color-wrapper');

    const colorTitle = document.createElement('span');
    colorTitle.textContent = "Choose Print Color";

    const bwLabel = document.createElement('label');
    const bwInput = document.createElement('input');
    bwInput.type = 'radio';
    bwInput.name = `color[${groupIndex}][${fileIndex}]`;
    bwInput.value = 'bw';
    bwInput.checked = true;
    bwLabel.appendChild(bwInput);
    bwLabel.appendChild(document.createTextNode('B&W'));

    const colorLabel = document.createElement('label');
    const colorInput = document.createElement('input');
    colorInput.type = 'radio';
    colorInput.name = `color[${groupIndex}][${fileIndex}]`;
    colorInput.value = 'color';
    colorLabel.appendChild(colorInput);
    colorLabel.appendChild(document.createTextNode('Color'));

    colorWrapper.appendChild(colorTitle);
    colorWrapper.appendChild(bwLabel);
    colorWrapper.appendChild(colorLabel);

    return colorWrapper;
}

// Helper function to create the side selector
function createSideSelector(groupIndex, fileIndex) {
    const sideWrapper = document.createElement('td');
    sideWrapper.classList.add('side-wrapper');

    const sideTitle = document.createElement('span');
    sideTitle.textContent = "Choose Print Side";

    const singleLabel = document.createElement('label');
    const singleInput = document.createElement('input');
    singleInput.type = 'radio';
    singleInput.name = `side[${groupIndex}][${fileIndex}]`;
    singleInput.value = 'single';
    singleInput.checked = true;
    singleLabel.appendChild(singleInput);
    singleLabel.appendChild(document.createTextNode('Single'));

    const dualLabel = document.createElement('label');
    const dualInput = document.createElement('input');
    dualInput.type = 'radio';
    dualInput.name = `side[${groupIndex}][${fileIndex}]`;
    dualInput.value = 'dual';
    dualLabel.appendChild(dualInput);
    dualLabel.appendChild(document.createTextNode('Dual'));

    sideWrapper.appendChild(sideTitle);
    sideWrapper.appendChild(singleLabel);
    sideWrapper.appendChild(dualLabel);

    return sideWrapper;
}

function createPageRangeSelector(fileIndex) {
    const pageRangeWrapper = document.createElement('td');
    pageRangeWrapper.classList.add('page-range-wrapper');

    const pageRangeTitle = document.createElement('span');
    pageRangeTitle.textContent = "Choose Page Range";

    const pageRangeSelect = document.createElement('select');
    pageRangeSelect.name = `pageRangeType[]`; // Ensure this matches Flask's expectation
    pageRangeSelect.innerHTML = `
        <option value="all">All Pages</option>
        <option value="custom">Custom Range</option>
        <option value="firstHalf">First Half</option>
        <option value="secondHalf">Second Half</option>
        <option value="evenPages">Even Pages</option>
        <option value="oddPages">Odd Pages</option>
    `;

    const customRangeDiv = document.createElement('div');
    customRangeDiv.style.display = 'none';

    const fromInput = document.createElement('input');
    fromInput.type = 'number';
    fromInput.name = `pageRangeFrom[]`; // Matches Flask expectation
    fromInput.min = 1;
    fromInput.placeholder = 'From';

    const toInput = document.createElement('input');
    toInput.type = 'number';
    toInput.name = `pageRangeTo[]`; // Matches Flask expectation
    toInput.min = 1;
    toInput.placeholder = 'To';

    customRangeDiv.appendChild(fromInput);
    customRangeDiv.appendChild(document.createTextNode(' to '));
    customRangeDiv.appendChild(toInput);

    pageRangeSelect.onchange = function() {
        if (this.value === 'custom') {
            customRangeDiv.style.display = 'inline';
        } else {
            customRangeDiv.style.display = 'none';
            fromInput.value = ''; // Clear custom range values
            toInput.value = '';
        }
    };

    // Validation to ensure "from" is less than or equal to "to"
    toInput.oninput = function() {
        if (parseInt(fromInput.value) > parseInt(toInput.value)) {
            toInput.setCustomValidity('The "To" value should be greater than or equal to "From" value.');
        } else {
            toInput.setCustomValidity('');
        }
    };

    fromInput.oninput = function() {
        if (parseInt(fromInput.value) > parseInt(toInput.value)) {
            toInput.setCustomValidity('The "To" value should be greater than or equal to "From" value.');
        } else {
            toInput.setCustomValidity('');
        }
    };

    pageRangeWrapper.appendChild(pageRangeTitle);
    pageRangeWrapper.appendChild(pageRangeSelect);
    pageRangeWrapper.appendChild(customRangeDiv);

    return pageRangeWrapper;
}



function areFilesSelected() {
    const lastFileInput = document.querySelector(`#file-group-${fileGroupCount} input[type="file"]`);
    return lastFileInput && lastFileInput.files.length > 0;
}

function updateCounter(button, action) {
    const counterInput = button.closest('.counter-wrapper').querySelector('.counter');
    let count = parseInt(counterInput.value);

    if (action === 'plus') {
        count++;
    } else if (action === 'minus' && count > 1) {
        count--;
    }

    counterInput.value = count;
}

function validateCounter(input) {
    input.value = input.value.replace(/\D/g, '');
    if (input.value === '' || parseInt(input.value) < 1) {
        input.value = 1;
    }
}

function updateMaxPageNumber(maxPages) {
    const fromInputs = document.querySelectorAll('input[name^="pageRangeFrom"]');
    const toInputs = document.querySelectorAll('input[name^="pageRangeTo"]');
    
    fromInputs.forEach(input => {
        input.max = maxPages;
    });
    
    toInputs.forEach(input => {
        input.max = maxPages;
        input.value = maxPages; // Set 'To' to max pages by default
    });
}

window.onload = function() {
    addFileInput();
}