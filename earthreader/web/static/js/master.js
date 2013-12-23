function scrollToElement(parentElement, childElement) {
	parentElement.scrollTop(parentElement.scrollTop() + childElement.offset().top - parentElement.offset().top);
	parentElement.scrollLeft(parentElement.scrollLeft() + childElement.offset().left - parentElement.offset().left);
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

function printError(xhr, statusText, error) {
	try {
		var json = JSON.parse(xhr.responseText);
		alert(json.error + '\n' + json.message);
	} catch (err) {
		alert(statusText + error);
	}
}

function changeFilter(event) {
	var target = $(event.target);
	var filter = target.attr('data-filter');
	closeMenu();

	$('[role=navigation] .persistent .current').removeClass('current');
	target.addClass('current');

	reloadEntries();
}

function clickComplementaryMenu(event) {
	var target = $(event.target);
	while (target.attr('data-action') === undefined) {
		target = target.parent();
	}

	var action = target.attr('data-action');
	closeSide();

	if (action === 'remove-this') {
		removeCurrentSelected();
	} else if (action === 'change-theme') {
		var theme_name = target.attr('data-theme-name');
		changeTheme(theme_name);
	} else if (action === 'mark-unread') {
		unreadCurrent();
	} else if (action === 'toggle-star') {
		toggleStarCurrent();
	}
}

function removeCurrentSelected() {
	var current = $('[role=navigation] .feedlist .current');
	var url;

	if (current.hasClass('header')) {
		current = current.parent();
	}
	url = current.attr('data-remove-feed-url') || current.attr('data-remove-category-url');
	if (url) {
		var parentMenu = current;
		while (parentMenu.hasClass('fold') === false) {
			parentMenu = parentMenu.parent();
			if (parentMenu.length === 0) {
				break;
			}
		}

		if (confirm('remove ' + current.text() + '\nAre you sure?') === true){
			$.ajax({
				'url': url,
				'type': 'delete',
			}).done(function(obj) {
				makeFeedList(obj, parentMenu);
			});
		}
	}
}

function unreadCurrent() {
	var current = $('[role=main] .entry.current');
	var markRead = current.find('.marks .read');
	var url = current.attr('data-read-url');
	var method = 'DELETE';

	$.ajax(url, {
		'type': method,
	}).done(function() {
		markRead.remove();
		current.find('.entry-title').removeClass('read');
	});
}

function toggleStarCurrent() {
	var current = $('[role=main] .entry.current');
	var markStar = current.find('.marks .star');
	var url = current.attr('data-star-url');
	var method;

	if (current.length === 0) {
		return;
	}

	if (markStar.length === 0) {
		method = 'PUT';
	} else {
		method = 'DELETE';
	}

	$.ajax(url, {
		'type': method,
	}).done(function() {
		if (markStar.length === 0) {
			markStar = $('<span>');
			markStar.addClass('star');
			current.find('.marks').append(markStar);
		} else {
			markStar.remove();
		}
	});


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
	while (target.hasClass('header') === false) {
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

	var data = target.serialize();
	var after = target.attr('data-after');
	var action = target.attr('action');
	try {
		var current = $('[role=navigation] .feedlist .current');
		if (target.hasClass('addFeed')) {
			action = current.attr('data-add-feed-url') ||
				current.parent().attr('data-add-feed-url') ||
				target.attr('action');
		} else if (target.hasClass('addCategory')) {
			action = current.attr('data-add-category-url') ||
				current.parent().attr('data-add-category-url') ||
				target.attr('action');
		}
	} catch (err) {
	}

	$.post(action,data).done(function(res) {
		if (current === null) {
			makeFeedList(res);
		} else {
			var fold = current.next();
			fold.html("");
			makeFeedList(res, fold);
		}
		target.each(function(){
			this.reset();
		});
	}).fail(function(xhr, status, err) {
		var json = xhr.responseJSON;
		alert(json.error + "\n" + json.message);
	});
}


var makeCategory = function(parentObj, obj) {
	var container = $('<li>');
	var header = $('<div>');
	var list = $('<ul>');
	var i;

	header.addClass('feed header');
	header.attr('role', 'link');
	container.attr('data-entries', obj.entries_url);
	if (obj.add_category_url) {
		container.attr('data-add-category-url', obj.add_category_url);
	}
	if (obj.add_feed_url) {
		container.attr('data-add-feed-url', obj.add_feed_url);
	}
	if (obj.remove_feed_url) {
		container.attr('data-remove-feed-url', obj.remove_feed_url);
	}
	if (obj.remove_category_url) {
		container.attr('data-remove-category-url', obj.remove_category_url);
	}
	if (obj.move_url) {
		container.attr('data-move-url', obj.move_url);
	}
	if (obj.path){
		container.attr('data-path', obj.path);
	}

	header.html(obj.title.link(obj.entries_url));

	var toggle = $('<span>');
	toggle.addClass('toggle');
	header.prepend(toggle);

	var handle = $('<span>');
	handle.addClass('handle');
	header.prepend(handle);

	header.attr('draggable', true);

	$.get(obj.feeds_url, function(obj) {
		for (i=0; i<obj.categories.length; i++) {
			makeCategory(list, obj.categories[i]);
		}
		for (i=0; i<obj.feeds.length; i++) {
			makeFeed(list, obj.feeds[i]);
		}
	});
	list.addClass('fold');
	header.on('dragstart', dragStart);
	header.on('dragover', dragOver);
	header.on('drop', drop);

	container.append(header);
	container.append(list);

	container.addClass('folder');
	parentObj.append(container);
};

var makeFeed = function(parentObj, obj) {
	var elem = $('<li>');
	elem.addClass('feed');
	elem.attr('data-entries', obj.entries_url);
	elem.attr('data-remove-feed-url', obj.remove_feed_url);
	elem.attr('data-path', obj.path);
	elem.attr('role', 'link');
	elem.html(obj.title.link(obj.entries_url));

	var handle = $('<span>');
	handle.addClass('handle');
	elem.prepend(handle);

	elem.attr('draggable', true);
	elem.on('dragstart', dragStart);

	parentObj.append(elem);
};

function makeFeedList(obj, target) {
	var feedList;
	var i;
  
	if (target && target.length !== 0) {
		feedList = target;
	} else {
		feedList = $('.allfeed.folder');
	}
	feedList.html("");

	for (i=0; i<obj.categories.length; i++) {
		makeCategory(feedList, obj.categories[i]);
	}
	for (i=0; i<obj.feeds.length; i++) {
		makeFeed(feedList, obj.feeds[i]);
	}
}

function refreshFeedList() {
	$.get(URLS.feeds, function(obj) {
		makeFeedList(obj);
	});
}

function dragStart(event) {
	if (!$(event.target).is('li')) {
		event.target = $(event.target).closest('li');
	}
	var target = $(event.target).attr('data-path');
	event.originalEvent.dataTransfer.setData('data-path', target);
}

function dragOver(event) {
	event.preventDefault();
}

function drop(event) {
	var dataPath = event.originalEvent.dataTransfer.getData('data-path');
	var target = $(event.target).closest('[data-move-url]');
	var moveUrl = target.attr('data-move-url') + '?from=' + dataPath;
	moveOutline(moveUrl);
}

function dropToHeader(event) {
	var dataPath = event.originalEvent.dataTransfer.getData('data-path');
	var moveUrl = URLS.feeds + '?from=' + dataPath;
	moveOutline(moveUrl);
}

function moveOutline(url) {
	$.ajax({
		url: url,
		type: 'put'
	}).done(function(){
		refreshFeedList();
	}).fail(printError);
}

function getAllEntries() {
	var all_feed = $('[role=navigation] .allfeed.header');
	$('[role=navigation] .allfeed .current').removeClass('current');
	all_feed.addClass('current');
	closeMenu();
	reloadEntries();
}

function appendEntry(entry) {
	var main = $('[role=main]');
	
	var article = $('<article>');
	var header = $('<div>');
	var time = $('<time>');
	var title = $('<span>');
	var marks = $('<div>');

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

	time.text(moment(entry.updated).fromNow());
	time.attr('title', moment(entry.updated).format('L'));
	header.append(time);

	title.text(entry.title);
	title.addClass('title');
	header.append(title);

	if (entry.read) {
		header.addClass('read');
	}
	if (entry.starred) {
		header.addClass('starred');
		var starMark = $('<span>');
		starMark.addClass('star');
		marks.append(starMark);
	}
	marks.addClass('marks');
	header.append(marks);

	article.append(header);
	main.append(article);
}

function getEntries(feed_url, filter) {
	var main = $('[role=main]');
	var requestUrl = feed_url;
	if (filter) {
		requestUrl += '?' + filter;
	}

	$.get(requestUrl, function(obj) {
		var feed_title = obj.title;
		var entries = obj.entries;
		var header = $('<header>');
		var h2 = $('<h2>');
		var refresh = $('<a>');

		main.html(null);

		h2.text(feed_title);
		header.append(h2);

		refresh.addClass('refresh');
		refresh.attr('role', 'button');
		refresh.attr('href', feed_url);
		refresh.text('crawl now');
		header.append(refresh);

		main.append(header);

		if (entries.length === 0) {
			var noEntry = $('<p>');
			noEntry.text('No more entry');
			main.append(noEntry);
		} else {
			for (var i=0; i<entries.length; i++) {
				appendEntry(entries[i]);
			}
		}

		if (obj.next_url) {
			var nextLoader = main.find('.nextPage');
			if (nextLoader.length === 0) {
				nextLoader = $('<div>');
				nextLoader.addClass('nextPage');
				nextLoader.text("Load next page");
			}
			nextLoader.attr('data-next-url', obj.next_url);
			main.append(nextLoader);
		}
		$(window).scrollTop(0);
	}).fail(printError);
}

function loadNextPage() {
	var main = $('[role=main]');
	var nextLoader = main.find('.nextPage');
	if (nextLoader === null) {
		return;
	}

	var nextUrl = nextLoader.attr('data-next-url');
	nextLoader.remove();

	$.get(nextUrl, function(obj) {
		var entries = obj.entries;
		for (var i=0; i<entries.length; i++) {
			appendEntry(entries[i]);
		}

		if (obj.next_url) {
			var nextLoader = $('<div>');
			nextLoader.addClass('nextPage');
			nextLoader.text("Load next page");
			nextLoader.attr('data-next-url', obj.next_url);
			main.append(nextLoader);
		} else {
			$('.nextPage').remove();
		}
	});
}

function autoNextPager(event) {
	var nextPage = $('[role=main] .nextPage');

	if (nextPage.length === 0) {
		return;
	}

	var screenBottom = $(window).scrollTop() + $(window).height();
	var prefetch_offset = $(window).height()/2;
	var pagerTop = nextPage.offset().top;

	if (screenBottom + prefetch_offset >= pagerTop) {
		loadNextPage();
	}
}

function reloadEntries() {
	var currentFilter = $('[role=navigation] .persistent .current');
	var currentFeed = $('[role=navigation] .feedlist .current');

	var filter = currentFilter.attr('data-filter');
	var url = currentFeed.attr('data-entries') || currentFeed.parent().attr('data-entries') || URLS.entries;

	getEntries(url, filter);
}

function clickFeed(event) {
	var target = $(event.target);
	var feedlist = $('[role=navigation] .feedlist');

	while (target.hasClass('feed') === false) {
		//toggle folding
		if (target.hasClass('toggle')) {
			target.parent().toggleClass('closed');
			return;
		}
		target = target.parent();
	}

	//set current marker
	feedlist.find('.current').removeClass('current');
	target.addClass('current');


	closeMenu();

	reloadEntries();
}

function clickEntry(event) {
	var target = $(event.target);
	var main = $('[role=main]');

	while (target.hasClass('entry-title') === false) {
		target = target.parent();
	}

	var entry = target.parent();
	var entry_url = entry.attr('data-entries');


	//close content
	var content = entry.find('.entry-content');
	if (content.length) {
		content.remove();
		return;
	}

	$.get(entry_url, function(obj) {
		var i;
		//set current marker
		main.find('.current').removeClass('current');
		target.parent().addClass('current');

		//remove content
		contents = main.find('.entry-content');
		for (i=0; i<contents.length; i++) {
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

		target.parent().attr('data-read-url', obj.read_url);
		target.parent().attr('data-star-url', obj.star_url);
		//read
		$.ajax({
			'type': 'put',
			'url': obj.read_url,
		}).done(function() {
			target.addClass('read');
		});

		$(window).scrollTop(entry.position().top);
	}).fail(printError);
}

function refreshFeed() {
	var target = $('[role=main] .refresh');
	var url = target.attr('href');
	target.text('requesting...');
	$.ajax(url, {'type': 'PUT'})
		.done(function() {
			target.remove();
		});
}

function clickLink(event) {
	var target = event.target;

	if (target.host === location.host) {
		//FIXME: ajax request
		event.preventDefault();
	} else {
		window.open(target.href);
		event.preventDefault();
	}
}

function keyboardShortcut(event) {
	if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
		return;
	}

	var main = $('[role=main]');
	var feedlist = $('[role=navigation] .feedlist');

	var nextEntry = function nextEntry() {
		var entry = main.find('.current').first();
		if (entry.length === 0) {
			main.find('.entry .entry-title').first().click();
			return;
		}
		var next = entry.next().first();
		if (next.length === 0) {
			return;
		}
		next.find('.entry-title').click();
	};

	var prevEntry = function prevEntry() {
		var entry = main.find('.current').first();
		if (entry.length === 0) {
			return;
		}
		var prev = entry.prev().last();
		if (prev.length === 0 || prev.hasClass('entry')) {
			//close current
			entry.click();
		}
		prev.find('.entry-title').click();
	};

	var nextFeed = function nextFeed() {
		var feeds = feedlist.find('.feed');
		if (feeds.filter('.current').length === 0) {
			feeds.first().click();
			return;
		}
		feeds.each(function (index) {
			if ($(this).hasClass('current') && (index + 1) < feeds.length) {
				feeds[index + 1].click();
				return false;
			}
		});
	};

	var prevFeed = function prevFeed() {
		var feeds = feedlist.find('.feed');

		if (feeds.first().hasClass('current')) {
			feedlist.find('.allfeed.header').click();
			return;
		}

		feeds.each(function (index) {
			if ($(this).hasClass('current')) {
				feeds[index - 1].click();
				return false;
			}
		});
	};

	var openInNewTab = function openInNewTab() {
		var read_on_web = main.find('.read-on-web');
		if (read_on_web) {
			window.open(read_on_web.attr('href'));
		}
	};

	switch (event.keyCode) {
		case 74: //j
			nextEntry();
			break;
		case 75: //k
			prevEntry();
			break;
		case 78: //n
			nextFeed();
			break;
		case 79: //o
			openInNewTab();
			break;
		case 80: //p
			prevFeed();
			break;
		case 82: //r
			reloadEntries();
			break;
		case 83: //s
			toggleStarCurrent();
			break;
		case 85: //u
        case 77: //m
			unreadCurrent();
			break;
		case 191: // /
			// ?
			if (event.shiftKey) {
				openManual();
			}
			break;
	}
}

function changeTheme(name) {
	if (name in THEMES === false) {
		return;
	}

	var theme = $('style.theme');
	theme.html("@import url('" + THEMES[name] + "');");
}

function openManual() {
	$('#manual').fadeIn();
}

function closeManual() {
	$('#manual').fadeOut();
}

$(function () {

	//moment.js language
	moment.lang(navigator.language.substr(0,2));

	var navi = $('[role=navigation]');
	var persistent = navi.find('.persistent');
	var feedlistHeader = navi.find('.allfeed.header');
	var feedlist = navi.find('.allfeed.folder');
	feedlistHeader.on('click', getAllEntries);
	feedlistHeader.on('click', getAllEntries);
	feedlistHeader.on('dragover', dragOver);
	feedlistHeader.on('drop', dropToHeader);
	feedlist.on('click', '.feed', clickFeed);
	persistent.on('click', '[data-filter]', changeFilter);
	persistent.on('click', '.header', toggleFolding);

	var main = $('[role=main]');
	main.on('click', '.entry-title', clickEntry);
	main.on('click', '.nextPage', loadNextPage);
	main.on('click', '.refresh', refreshFeed);

	var side = $('[role=complementary]');
	side.on('click', '[data-action]', clickComplementaryMenu);

	$(document).on('click', '.off-canvas-menu', toggleMenu);
	$(document).on('click', '.off-canvas-side', toggleSide);
	$(document).on('click', 'a', clickLink);

	$(document).on('submit', 'form.addFeed, form.addCategory', processForm);
	$(window).on('keydown', keyboardShortcut);
	$(window).on('scroll', autoNextPager);

	$('#manual').click(closeManual);

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

	$('[role=navigation] .persistent .unread').addClass('current');
	$('[role=navigation] .feedlist .allfeed.header').addClass('current');
	refreshFeedList();
	reloadEntries();


	//Chrome rendering bug
	$('.off-canvas-side')
		.hide()
		.delay('slow')
		.fadeIn('fast');
});
