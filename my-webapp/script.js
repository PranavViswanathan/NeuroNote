// JavaScript for handling UI events and fetching data from the backend

document.addEventListener('DOMContentLoaded', function() {
    // Get references to the UI elements
    var addPageButton = document.getElementById('add-page-button');
    var prevButton = document.getElementById('prev-button');
    var nextButton = document.getElementById('next-button');
    var pageSelect = document.getElementById('page-select');
    var pageContainer = document.getElementById('page-container');
    var blockContainer = document.getElementById('block-container');
    var addBlockButton = document.getElementById('add-block-button');
  
    //
  


  
    // Add event listeners for the navigation buttons
    prevButton.addEventListener('click', function() {
      fetchPrevBlock();
    });
    nextButton.addEventListener('click', function() {
      fetchNextBlock();
    });
  
      // Fetch the previous block of text and update the UI
  function fetchPrevBlock() {
    var currentBlockId = parseInt(blockContainer.dataset.blockId);
    if (currentBlockId > 1) {
      fetch(`/api/blocks/${currentBlockId - 1}`)
        .then(function(response) {
          return response.json();
        })
        .then(function(block) {
          displayBlock(block);
          updateButtons(block.id);
        });
    }
  }

  // Fetch the next block of text and update the UI
  function fetchNextBlock() {
    var currentBlockId = parseInt(blockContainer.dataset.blockId);
    fetch(`/api/blocks/${currentBlockId + 1}`)
      .then(function(response) {
        return response.json();
      })
      .then(function(block) {
        displayBlock(block);
        updateButtons(block.id);
      });
  }

  // Display a block of text in the UI
  function displayBlock(block) {
    blockContainer.innerHTML = block.text;
    blockContainer.dataset.blockId = block.id;
  }

  // Enable or disable the navigation buttons based on the current block id
  function updateButtons(blockId) {
    if (blockId === 1) {
      prevButton.disabled = true;
    } else {
      prevButton.disabled = false;
    }
    // Assume there are more blocks after the current one
    nextButton.disabled = false;
  }
});
