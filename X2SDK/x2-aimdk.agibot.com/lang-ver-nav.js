$(document).ready(function() {
	let [a, lang_cur, ver_cur] = window.location.pathname.split('/', 3);
	var nav_div = $('<div id="lang-ver-nav">');
	$('<style>').text(`
footer > #lang-ver-nav {
position: fixed;
right: 20px;
bottom: 50px;
z-index:999;
height: auto;
width: auto;
max-width: 25em;
max-height: calc(100% - 100px);
font-size: 0.8rem;
padding: 0 10px;
overflow-y: auto;
color: rgb(128, 128, 128);
background-color: rgba(39,39,37,0.9);
border-radius: 3px;
}
#lang-ver-nav header {
display: flex;
flex-flow: row;
gap: 0.5em;
align-items: center;
cursor: pointer;
position: sticky;
top: 0px;
font-size: 1.125em;
}
#nav-logo-box {
background-image: url("/nav-logo.en.png");
display: flex;
flex: 0 1 auto;
padding: 24px 20px 0 0;
background-repeat: no-repeat;
background-size: 100px;
}
#nav-logo-box.fullwidth {
padding-left: 82px;
}
#lang-ver-nav img.nav-logo {
max-height: 1.5em;
width: auto;
padding: 0;
margin: -0.2em 0.75em 0 0;
flex: 0 1 auto;
}
#lang-ver-nav .fa {
color: rgb(128,128,128);
margin-right: 0.25em;
vertical-align: middle;
height: 1.125em;
}
header > span:first-of-type {
margin-left: auto;
}
header > span {
color: #27ae60;
font-size: 1.125em;
margin-left: 10px;
padding: 0.75em 0;
line-height: 1em;
text-overflow: ellipsis;
flex: 0 0 auto;
white-space: nowrap;
}
main.closed {
display:none;
}
main {
padding: 5px 5px 15px;
margin-top: 5px;
}
#lang-ver-nav dl {
margin: 0;
padding: 0;
min-height: 4.5em;
}
#lang-ver-nav dt {
display: block;
padding: 0;
margin: 0;
background: none;
border: none;
font-size: inherit;
}
#lang-ver-nav dl > dd {
display: inline-block;
margin: 0px;
line-height: 1.25em;
}
#lang-ver-nav dd a {
text-decoration: none;
color: rgb(252, 252, 252);
padding: 6px;
display: inline-block;
}
	`).appendTo('head');

	$('footer').append(nav_div);

	$(`
<header>
<span id="nav-logo-box"></span>
<span class="language"><i class="fa fa-language"></i>${lang_cur}</span>
<span class="version"><i class="fa fa-code-branch"></i>${ver_cur}</span>
<span class="caret"><i class="fa fa-caret-down"></i></span>
</header>
<main class="closed">
<dl class="languages">
<dt>Languages</dt>
</dl>
<dl class="versions">
<dt>Versions</dt>
</dl>
<dl class="downloads">
<dt>Downloads</dt>
</dl>
</main>
`).appendTo(nav_div);
	function addDownload(label, url) {
		var dd = $('<dd>');
		var a = $('<a>');
		a.attr('href', url);
		a.attr('target', '_blank');
		a.html(label);
		a.appendTo(dd);
		dd.appendTo('dl.downloads');
	}
	$.getJSON('/sdk-downloads.json', function(sdk_list) {
		sdk_list.forEach(function(item) {
			var filename = item.src.split('/').pop();
			addDownload(item.label, '/downloads/' + filename);
		});
	});
	function addVersion(vername) {
		var dd = $('<dd>');
		var a = $('<a>');
		a.attr('href', window.location.href.replace(`/${ver_cur}/`, `/${vername}/`));
		if (vername == ver_cur) {
			a.html(`<strong>${vername}</strong>`);
		} else {
			a.html(vername);
		}
		a.appendTo(dd)
		dd.appendTo('dl.versions');
	}
	if (lang_cur in nav_data) {
		nav_data[lang_cur].forEach(addVersion);
	}
	function addLang(langname) {
		var dd = $('<dd>');
		var a = $('<a>');
		a.attr('href', window.location.href.replace(`/${lang_cur}/`, `/${langname}/`));
		if (langname == lang_cur) {
			a.html(`<strong>${langname}</strong>`);
		} else {
			a.html(langname);
		}
		a.appendTo(dd)
		dd.appendTo('dl.languages')
	}
	Object.keys(nav_data).toSorted().forEach(addLang);
	$('header').on('click', function() {$('main').toggleClass('closed');$('#nav-logo-box').toggleClass('fullwidth')})
});
var nav_data={"en": ["latest"], "zh-cn": ["latest"]}

var nav_data={"en": ["latest", "v0.9.0", "v0.8.2", "v0.8.1"], "zh-cn": ["latest", "v0.9.0", "v0.8.2", "v0.8.1"]}