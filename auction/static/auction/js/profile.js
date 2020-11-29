function updateToggle() {
    var content = document.getElementById("update-nupp");
    let toggleFields = document.getElementsByClassName('toggle')
    console.log(toggleFields)
    for (let i = 0; i < toggleFields.length; i++) {
        if (toggleFields[i].checked == true) {
            content.style.display = "block";
            break;
        }
        else {
            content.style.display = "none";
        }
    }
}