function folderToggle(event) {
	var target = event.target;
	while (target.nodeName !== 'HEADER') {
		target = target.parentElement;
		if (target === null) {
			return;
		}
	}

	if (target.classList.contains('closed')) {
		target.classList.remove('closed');
	} else {
		target.classList.add('closed');
	}
}

function init() {
	var navi = document.querySelector('[role=navigation]');
	navi.addEventListener('click', folderToggle, false);
}

window.addEventListener('DOMContentLoaded', init, false);
