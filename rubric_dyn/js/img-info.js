// set foto exif information from json object if there
// cem, 2016-02-12
// cem, 2016-04-29 update toggle

function toggle_info(ev) {
    var node = ev.target

    var pre = node.parentElement.getElementsByTagName('pre')[0];

    if (pre.style.display == "block") {
        pre.style.display = "none";
    }
    else {
        pre.style.display = "block";
    }
}

function toggle_info2(ev) {
    var node = ev

    var fig_i = node.parentElement.getElementsByTagName('div')[1];
    //alert("FOO");
    if (fig_i.style.display == "block") {
        fig_i.style.display = "none";
    }
    else {
        fig_i.style.display = "block";
    }
}

// get figures
var figures = document.getElementsByTagName('figure');

for (var i = 0; i < figures.length; i++) {
    var fig = figures[i]
    var img = fig.getElementsByTagName('img');

    var img_src = img[0].getAttribute("src");

    // check if image has exif data (stored in img_exifs_json obj.)
    for (var key in img_exifs_json) {
        if (key == img_src) {

            // create pre text
            var pre = document.createElement('pre');
            pre.innerHTML = img_exifs_json[key];
            //pre.className = "exiftext";
            var figcapt = fig.getElementsByTagName('figcaption')[0];
            figcapt.appendChild(pre);

            // create "button"
            var img_button = document.createElement('img');
            img_button.src = "/media/info.png";
            img_button.title = "Show image information (EXIF)"
            img_button.addEventListener("click", toggle_info);
            figcapt.appendChild(img_button);
        }
    }
}
