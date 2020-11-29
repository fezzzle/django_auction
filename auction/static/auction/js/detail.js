myFunction(document.getElementById("sml_img"))
let jsonCtx = JSON.parse(JSON.parse(document.getElementById('json_ctx').textContent));

(function countdownTimeStart(){
    
    var auctionEndStamp = jsonCtx['auction_end_stamp'];

    // Get todays date and time, convert to string, get only 10 digits
    var now = new Date().getTime();
    
    // Find the distance between now an the count down date
    var distance = auctionEndStamp - now;
    
    // Time calculations for days, hours, minutes and seconds
    var hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
    var seconds = Math.floor((distance % (1000 * 60)) / 1000);
    
    // Output the result in an element with id="demo"
    document.getElementById("clock").innerHTML = hours + "h "
    + minutes + "m " + seconds + "s ";
    
    // If the count down is over, write some text 
    if (distance < 0) {
        document.getElementById("clock").innerHTML = "EXPIRED";
    }
    setTimeout(countdownTimeStart, 1000);

})();

// IMG CONTAINER
function myFunction(imgs) {
    // Get the expanded image
    var expandImg = document.getElementById("expandedImg");

    // Use the same src in the expanded image as the image being clicked on from the grid
    expandImg.src = imgs.src;

    // Show the container element (hidden with CSS)
    expandImg.parentElement.style.display = "block";
}