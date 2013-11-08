function scrollToElement(parentElement, childElement) {
	parentElement.scrollTop(parentElement.scrollTop() + childElement.offset().top - parentElement.offset().top);
	parentElement.scrollLeft(parentElement.scrollLeft() + childElement.offset().left - parentElement.offset().left);
}

//FIXME: delete these
function getJSON(url, onSuccess, onFail) {
	var xhr = new XMLHttpRequest();
	xhr.open('get', url);
	xhr.onreadystatechange = function() {
		if (xhr.readyState !== 4) {
			return;
		}

		if (xhr.status === 200) {
			if (onSuccess instanceof Function) {
				var obj = JSON.parse(xhr.responseText);
				(onSuccess)(obj);
			}
		} else {
			if(onFail instanceof Function) {
				(onFail)(xhr);
			} else {
				try {
					var json = JSON.parse(xhr.responseText);
					var error = json.error;
					var message = json.message;
					alert(error + '\n' + message);
				}catch(err) {
					alert(xhr.statusText);
				}
			}
		}
	}
	xhr.send();
}

function deleteJSON(url, onSuccess, onFail) {
	var xhr = new XMLHttpRequest();
	xhr.open('post', url + '?_method=DELETE');
	xhr.onreadystatechange = function() {
		if (xhr.readyState !== 4) {
			return;
		}

		if (xhr.status === 200) {
			if (onSuccess instanceof Function) {
				var obj = JSON.parse(xhr.responseText);
				(onSuccess)(obj);
			}
		} else {
			if(onFail instanceof Function) {
				(onFail)(xhr);
			} else {
				try {
					var json = JSON.parse(xhr.responseText);
					var error = json.error;
					var message = json.message;
					alert(error + '\n' + message);
				}catch(err) {
					alert(xhr.statusText);
				}
			}
		}
	}
	xhr.send();
}

function post(url, parameter, onSuccess, onFail) {
	var xhr = new XMLHttpRequest();
	xhr.open('post', url);
	xhr.setRequestHeader("Content-type","application/x-www-form-urlencoded");
	xhr.onreadystatechange = function() {
		if (xhr.readyState !== 4) {
			return;
		}

		if (xhr.status === 200) {
			if (onSuccess instanceof Function) {
				var obj = JSON.parse(xhr.responseText);
				(onSuccess)(obj);
			}
		} else {
			if(onFail instanceof Function) {
				(onFail)(xhr);
			}
		}
	}
	xhr.send(parameter);
}

function serializeForm(form) {
	//FIXME
	var elements = form.querySelectorAll('input, textarea, select');
	var serialized = [];

	for (var i=0; i<elements.length; i++) {
		if (elements[i].name) {
			var name = encodeURIComponent(elements[i].name);
			var value = encodeURIComponent(elements[i].value);
			serialized.push(name + '=' + value);
		}
	}

	return serialized.join('&');
}

function resizer(event) {
	var name = event.animationName;

	if (name === "big") {
		document.body.removeClass('menu-open');
	} else if (name === "small") {
		document.body.removeClass('menu-open');
		document.body.removeClass('side-open');
	}
}

function clickPersistentMenu(event) {
	var target = $(event.target);
	var action = target.attr('data-action');
	closeMenu();

	if (action === 'all') {
		getAllEntries();
	}
}

function clickComplementaryMenu(event) {
	var target = $(event.target);
	if (["input", "textarea"].indexOf(target.localName) >= 0) {
		return;
	}

	while (target.attr('data-action') == null) {
		target = target.parentElement;
		if (target === null) {
			return;
		}
	}

	var action = target.attr('data-action');
	closeSide();

	if (action === 'remove-this') {
		removeCurrentSelected();
	} else if (action === 'change-theme') {
		var theme_name = target.attr('data-theme-name');
		changeTheme(theme_name);
	}
}

function removeCurrentSelected() {
	var current = $('[role=navigation] .current');

	var url = current.attr('data-remove-feed-url') || current.attr('data-remove-category-url');
	if (url) {
		var parentMenu = current;
		while (parentMenu.classList.contains('fold') == false) {
			parentMenu = parentMenu.parentElement;
			if (parentMenu == null) {
				break;
			}
		}

		deleteJSON(url, function(obj) {
			makeFeedList(obj, parentMenu);
		});
	}
}

function toggleMenu(event) {
	closeSide();
	$(document.body).toggleClass('menu-open');
}

function toggleSide(event) {
	closeMenu();
	$(document.body).toggleClass('side-open');
}

function toggleFolding(event) {
	var target = $(event.target);
	while (target.hasClass('header') == false) {
		target = target.parent();
		if (target === null) {
			return;
		}
	}

	target.toggleClass('closed');
}

function closeMenu() {
	$(document.body).removeClass('menu-open');
}

function closeSide() {
	$(document.body).removeClass('side-open');
}

function processForm(event) {
	var target = $(event.target);
	event.preventDefault();

	var data = serializeForm(target);
	var after = target.attr('data-after');
	if (after === "makeFeedList") {
		var action = target.action;
		try {
			var current = $('[role=navigation] .feedlist .current');
			if (target.attr('data-action') === 'addFeed') {
				action = current.attr('data-add-feed-url');
			} else if (target.attr('data-action') === 'addCategory') {
				action = current.attr('data-add-category-url') ||
					current.parent().prev().attr('data-add-category-url') ||
					target.attr('action');
			}
		} catch (err) {
		}
		post(action, data, function(res) {
			if (current == null) {
				makeFeedList(res);
			} else {
				var fold = current.next();
				fold.html("");
				//makeCategory(fold, res);
				makeFeedList(res, fold);
			}
			target.reset();
		});
	} else {
		post(target.action, data, function(res) {
			alert(res);
			target.reset();
		});
	}
}


var makeCategory = function(parentObj, obj) {
	var header = $('<li>');
	var list = $('<li>');

	header.addClass('header');
	header.addClass('feed');
	header.attr('role', 'link');
	header.attr('data-entries', obj.entries_url);
	if (obj.add_category_url) {
		header.attr('data-add-category-url', obj.add_category_url);
	}
	if (obj.add_feed_url) {
		header.attr('data-add-feed-url', obj.add_feed_url);
	}
	if (obj.remove_feed_url) {
		header.attr('data-remove-feed-url', obj.remove_feed_url);
	}
	if (obj.remove_category_url) {
		header.attr('data-remove-category-url', obj.remove_category_url);
	}

	header.text(obj.title);

	var toggle = $('<span>');
	toggle.addClass('toggle');
	header.prepend(toggle);

	var handle = $('<span>');
	handle.addClass('handle');
	header.prepend(handle);

	header.attr('draggable', true);

	list.addClass('fold');

	var ul = $('<ul>');
	getJSON(obj.feeds_url, function(obj) {
		for (var i=0; i<obj.categories.length; i++) {
			makeCategory(ul, obj.categories[i]);
		}
		for (var i=0; i<obj.feeds.length; i++) {
			makeFeed(ul, obj.feeds[i]);
		}
	});

	list.append(ul);

	parentObj.append(header);
	parentObj.append(list);
};

var makeFeed = function(parentObj, obj) {
	var elem = $('<li>');
	elem.addClass('feed');
	elem.attr('data-entries', obj.entries_url);
	elem.attr('data-remove-feed-url', obj.remove_feed_url);
	elem.attr('role', 'link');
	elem.text(obj.title);

	var handle = $('<span>');
	handle.addClass('handle');
	elem.prepend(handle);

	elem.attr('draggable', true);

	parentObj.append(elem);
};

function makeFeedList(obj, target) {
	var feedList;
	if (target) {
		feedList = target;
	} else {
		feedList = $('.feedlist');
	}
	feedList.html("");

	for (var i=0; i<obj.categories.length; i++) {
		makeCategory(feedList, obj.categories[i]);
	}
	for (var i=0; i<obj.feeds.length; i++) {
		makeFeed(feedList, obj.feeds[i]);
	}
}

function refreshFeedList() {
	getJSON(URLS.feeds, makeFeedList);
}

function getAllEntries() {
	var all_feed = $('[role=navigation] [data-action=all]');
	var list = $('[role=navigation] .current');
	for (var i=0; i<list.length; i++) {
		list[i].removeClass('current');
	}
	all_feed.addClass('current');
	getEntries(URLS.entries);
}

function appendEntry(entry) {
	var main = $('[role=main]');
	
	var article = $('<article>');
	var header = $('<div>');
	var time = $('<time>');
	var title = $('<span>');

	article.addClass('entry');
	article.attr('data-entries', entry.entry_url);

	header.addClass('entry-title');
	header.attr('role', 'button');

	if (entry.feed) {
		var category = $('<span>');
		category.addClass('feed');
		category.text(entry.feed.title);
		header.append(category);
	}

	time.text(entry.updated);
	header.append(time);

	title.text(entry.title);
	title.addClass('title');
	header.append(title);

	article.append(header);
	main.append(article);
}

function getEntries(feed_url) {
	var main = $('[role=main]');

	getJSON(feed_url, function(obj) {
		main.html(null);

		var feed_title = obj.title;
		var entries = obj.entries;

		var header = $('<header>');
		var h2 = $('<h2>');
		header.append(h2);
		h2.text(feed_title);

		main.append(header);

		for (var i=0; i<entries.length; i++) {
			appendEntry(entries[i]);
		}

		if (obj.next_url) {
			var nextLoader = main.find('.nextPage');
			if (nextLoader.length == 0) {
				nextLoader = $('<div>');
				nextLoader.addClass('nextPage');
				nextLoader.text("Load next page");
				nextLoader.onclick = loadNextPage;
			}
			nextLoader.attr('data-next-url', obj.next_url);
			main.append(nextLoader);
		}
		main.scrollTop(0);
	});
}

function loadNextPage() {
	var main = $('[role=main]');
	var nextLoader = main.find('.nextPage');
	if (nextLoader == null) {
		return;
	}

	getJSON(nextLoader.attr('data-next-url'), function(obj) {
		var entries = obj.entries;
		for (var i=0; i<entries.length; i++) {
			appendEntry(entries[i]);
		}

		if (obj.next_url) {
			var nextLoader = main.find('.nextPage');
			if (nextLoader == null) {
				nextLoader = $('<div>');
				nextLoader.addClass('nextPage');
				nextLoader.text("Load next page");
			}
			nextLoader.attr('data-next-url', obj.next_url);
			main.append(nextLoader);
		} else {
			$('.nextPage').remove();
		}
	});
}

function autoNextPager(event) {
	//FIXME
	var main = $('[role=main]');
	var nextPage = main.find('.nextPage');

	if (nextPage.length == 0) {
		return;
	}

	var scroll_bottom = main[0].scrollTop + main[0].offsetHeight;
	var nextPage_bottom = nextPage[0].offsetTop + nextPage[0].offsetHeight;

	if (scroll_bottom >= nextPage_bottom) {
		loadNextPage();
	}
}

function clickFeed(event) {
	var target = $(event.target);
	var navi = $('[role=navigation]');

	//toggle folding
	if (target.hasClass('toggle')) {
		target.parent().toggleClass('closed');
		return;
	}

	//set current marker
	navi.find('.current').removeClass('current');
	target.addClass('current');

	var url = target.attr('data-entries');

	closeMenu();

	getEntries(url);
}

function clickEntry(event) {
	var target = event.target;
	var main = $('[role=main]');

	while (target.classList.contains('entry-title') === false) {
		target = target.parentElement;
		if (target === null) {
			return;
		}
	}

	var entry = $(target.parentElement);
	var entry_url = entry.attr('data-entries');


	//close content
	var content = entry.find('.entry-content');
	if (content.length) {
		content.remove();
		return;
	}

	getJSON(entry_url, function(obj) {
		//set current marker
		var list = main.find('.current');
		for (var i=0; i<list.length; i++) {
			list[i].removeClass('current');
		}
		target.parentElement.addClass('current');

		//remove content
		contents = main.find('.entry-content');
		for (var i=0; i<contents.length; i++) {
			contents[i].parentElement.removeChild(contents[i]);
		}

		var wrapper = $('<div>');
		var title = $('<h1>');
		var content = $('<div>');
		var bottom_bar = $('<div>');
		var read_on_web = $('<a>');

		title.html(obj.title.link(obj.permalink));
		content.html(obj.content);

		bottom_bar.addClass('bottom-bar');
		read_on_web.attr('href', obj.permalink);
		read_on_web.addClass('read-on-web');
		read_on_web.text("Read on web");
		bottom_bar.append(read_on_web);

		wrapper.addClass('entry-content');
		wrapper.append(title);
		wrapper.append(content);
		wrapper.append(bottom_bar);
		entry.append(wrapper);

		scrollToElement(main, entry);
	});
}

function clickLink(event) {
	var target = event.target;

	if (target.host != location.host) {
		window.open(target.href);
		event.preventDefault();
	}
}

function keyboardShortcut(event) {
	if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
		return;
	}

	var main = $('[role=main]');

	switch (event.keyCode) {
		case 74: //j
			var entry = main.find('.current').first();
			if (entry.length == 0) {
				main.find('.entry .entry-title').first().click();
				return;
			}
			var next = entry.next().first();
			if (next.length == 0) {
				return;
			}
			next.find('.entry-title').click();
			break;
		case 75: //k
			var entry = main.find('.current').first();
			if (entry.length == 0) {
				return;
			}
			var prev = entry.prev().last();
			if (prev.length == 0 || prev.hasClass('entry')) {
				//close current
				entry.click();
			}
			prev.find('.entry-title').click();
			break;
		case 79: //o
			var read_on_web = main.find('.read-on-web');
			if (read_on_web) {
				window.open(read_on_web.attr('href'));
			}
	}
}

function changeTheme(name) {
	if (name in THEMES == false) {
		return;
	}

	var theme = $('style.theme');
	theme.html("@import url('" + THEMES[name] + "');");
}

$(function () {
	var navi = $('[role=navigation]');
	var persistent = navi.find('.persistent');
	navi.on('click', clickFeed);
	persistent.on('click', '[data-action]', clickPersistentMenu);
	persistent.on('click', toggleFolding);

	var main = $('[role=main]');
	main.on('click', clickEntry);
	main.on('scroll', autoNextPager);

	var side = $('[role=complementary]');
	side.on('click', clickComplementaryMenu);

	$(document).on('click', '.off-canvas-menu', toggleMenu);
	$(document).on('click', '.off-canvas-side', toggleSide);
	$(document).on('click', 'a', clickLink);

	$(document).on('submit', 'form', processForm);
	$(document).on('keydown', keyboardShortcut);

	//FIXME: clean it
    var animationEnd;
    if (document.body.style.animation !== undefined) {
        animationEnd = 'animationend';
    } else if (document.body.style.MozAnimation !== undefined) {
        animationEnd = 'animaionend';
    } else if (document.body.style.webkitAnimation !== undefined) {
        animationEnd = 'webkitAnimationEnd';
    } else if (document.body.style.OAnimtion !== undefined) {
        animationEnd = 'oAnimationEnd';
    } else if (document.body.style.msAnimation !== undefined) {
        animationEnd = 'MSAnimaionEnd';
    }
    $(document.body).on(animationEnd, resizer);

	refreshFeedList();
	getAllEntries();
});
