var freshtime=1000*3;
var displaytime=4000;
var displaytime_error=1000*60*5;

Date.prototype.format = function(format) {  
    /* 
     * eg:format="yyyy-MM-dd hh:mm:ss"; 
     */  
    var o = {  
        "M+" : this.getMonth() + 1, // month  
        "d+" : this.getDate(), // day  
        "h+" : this.getHours(), // hour  
        "m+" : this.getMinutes(), // minute  
        "s+" : this.getSeconds(), // second  
        "q+" : Math.floor((this.getMonth() + 3) / 3), // quarter  
        "S" : this.getMilliseconds()  
        // millisecond  
    }  
  
    if (/(y+)/.test(format)) {  
        format = format.replace(RegExp.$1, (this.getFullYear() + "").substr(4  
                        - RegExp.$1.length));  
    }  
  
    for (var k in o) {  
        if (new RegExp("(" + k + ")").test(format)) {  
            format = format.replace(RegExp.$1, RegExp.$1.length == 1  
                            ? o[k]  
                            : ("00" + o[k]).substr(("" + o[k]).length));  
        }  
    }  
    return format;  
}  

jQuery.cookie = function(name, value, options) {
    if (typeof value != 'undefined') { // name and value given, set cookie
        options = options || {};
        if (value === null) {
            value = '';
            options = $.extend({}, options); // clone object since it's unexpected behavior if the expired property were changed
            options.expires = -1;
        }
        var expires = '';
        if (options.expires && (typeof options.expires == 'number' || options.expires.toUTCString)) {
            var date;
            if (typeof options.expires == 'number') {
                date = new Date();
                date.setTime(date.getTime() + (options.expires * 24 * 60 * 60 * 1000));
            } else {
                date = options.expires;
            }
            expires = '; expires=' + date.toUTCString(); // use expires attribute, max-age is not supported by IE
        }
        // NOTE Needed to parenthesize options.path and options.domain
        // in the following expressions, otherwise they evaluate to undefined
        // in the packed version for some reason...
        var path = options.path ? '; path=' + (options.path) : '';
        var domain = options.domain ? '; domain=' + (options.domain) : '';
        var secure = options.secure ? '; secure' : '';
        document.cookie = [name, '=', encodeURIComponent(value), expires, path, domain, secure].join('');
    } else { // only name given, get cookie
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
};


$(document).ready(function() {
	
	calculateHeight();
	var location_url = location.href ;
	if(location_url.indexOf("systems")==-1&&location_url.indexOf("user")==-1){
		var show_mini=$.cookie('mini');
		if(show_mini&&show_mini!=null){
			if(show_mini=="true"){
				 $('#main-menu').addClass('mini');
				 $('#main-menu-wrapper ul li').addClass('.message-tooltip');
				 $('#main-menu-wrapper ul li').tooltip('toggle');
				 $('#main-menu-wrapper ul li').tooltip('hide');
				 $('.page-content').addClass('condensed');
				 $('.scrollup').addClass('to-edge');
				 $('.header-seperation').hide();
				 $('.footer-widget').hide(); 
				 $('.header-seperation-small').show();
				 
			}else{
				 $('#main-menu-wrapper ul li').removeClass('.message-tooltip');
				 $('#main-menu').removeClass('mini');
				 $('.page-content').removeClass('condensed');
				 $('.scrollup').removeClass('to-edge');
				 $('.header-seperation').show();
				 $('.header-seperation-small').hide();
				 //Bug fix - In high resolution screen it leaves a white margin
				 $('.header-seperation').css('height','61px');
				 $('.footer-widget').show(); 
			}
		}
	}
	
	$(".remove-widget").click(function() {
		$(this).parent().parent().parent().addClass('animated fadeOut');
		$(this).parent().parent().parent().attr('id', 'id_a');

		//$(this).parent().parent().parent().hide();
		 setTimeout( function(){
			$('#id_a').remove();
		 },400);
		return false;
	});

	$(".create-folder").click(function() {
		$('.folder-input').show();
		return false;
	});

	$(".folder-name").keypress(function (e) {
        if(e.which == 13) {
			 $('.folder-input').hide();
			 $( '<li><a href="#"><div class="status-icon green"></div>'+  $(this).val() +'</a> </li>' ).insertBefore( ".folder-input" );
			 $(this).val('');
		}
    });

	$("#menu-collapse").click(function() {
		if($('.page-sidebar').hasClass('mini')){
			$('.page-sidebar').removeClass('mini');
			$('.page-content').removeClass('condensed-layout');
			$('.footer-widget').show();
		}
		else{
			$('.page-sidebar').addClass('mini');
			$('.page-content').addClass('condensed-layout');
			$('.footer-widget').hide();
			calculateHeight();
		}
	});

	$(".inside").children('input').blur(function(){
		$(this).parent().children('.add-on').removeClass('input-focus');
	})

	$(".inside").children('input').focus(function(){
		$(this).parent().children('.add-on').addClass('input-focus');
	})

	$(".input-group.transparent").children('input').blur(function(){
		$(this).parent().children('.input-group-addon').removeClass('input-focus');
	})

	$(".input-group.transparent").children('input').focus(function(){
		$(this).parent().children('.input-group-addon').addClass('input-focus');
	})

	$(".bootstrap-tagsinput input").blur(function(){
		$(this).parent().removeClass('input-focus');
	})

	$(".bootstrap-tagsinput input").focus(function(){
		$(this).parent().addClass('input-focus');
	})

	//popover 弹出信息请全部写到这里。
	$('#my-task-list').popover({
        html : true,
        content: function() {
          return $('#notification-list').html();
        }
    });
	
    $('.content').popover({
        html: true,
        content: function() {
            return $(this).siblings('.popover-content').html();
        },
        trigger:'hover',
        selector: 'table .table-popover-list'
    });

//*********************************** BEGIN CHAT POPUP*****************************
/*	 $('.chat-menu-toggle').sidr({
		name:'sidr',
		side: 'right',
		complete:function(){
		}
	});
	$(".simple-chat-popup").click(function(){
		$(this).addClass('hide');
		$('#chat-message-count').addClass('hide');
	});

	setTimeout( function(){
		$('#chat-message-count').removeClass('hide');
		$('#chat-message-count').addClass('animated bounceIn');
		$('.simple-chat-popup').removeClass('hide');
		$('.simple-chat-popup').addClass('animated fadeIn');
	},5000);
	setTimeout( function(){
		$('.simple-chat-popup').addClass('hide');
		$('.simple-chat-popup').removeClass('animated fadeIn');
		$('.simple-chat-popup').addClass('animated fadeOut');
	},8000);*/

//*********************************** END CHAT POPUP*****************************

//**********************************BEGIN MAIN MENU********************************
	jQuery('.page-sidebar li > a').on('click', function (e) {
            if ($(this).next().hasClass('sub-menu') == false) {
                return;
			}
			alert("Hi!")
     		var parent = $(this).parent().parent();

            parent.children('li.open').children('a').children('.arrow').removeClass('open');
            parent.children('li.open').children('.sub-menu').slideUp(200);
            parent.children('li.open').removeClass('open');

            var sub = jQuery(this).next();
            if (sub.is(":visible")) {
                jQuery('.arrow', jQuery(this)).removeClass("open");
                jQuery(this).parent().removeClass("open");
                sub.slideUp(200, function () {
                    handleSidenarAndContentHeight();
                });
            } else {
                jQuery('.arrow', jQuery(this)).addClass("open");
                jQuery(this).parent().addClass("open");
                sub.slideDown(200, function () {
                    handleSidenarAndContentHeight();
                });
            }

            e.preventDefault();
        });
//**********************************END MAIN MENU********************************
//***********************************BEGIN Fixed Menu*****************************


//***********************************BEGIN Grids*****************************
		 $('.grid .tools a.remove').on('click', function () {
            var removable = jQuery(this).parents(".grid");
            if (removable.next().hasClass('grid') || removable.prev().hasClass('grid')) {
                jQuery(this).parents(".grid").remove();
            } else {
                jQuery(this).parents(".grid").parent().remove();
            }
        });

        $('.grid .tools a.reload').on('click', function () {
            var el =  jQuery(this).parents(".grid");
            blockUI(el);
			window.setTimeout(function () {
               unblockUI(el);
            }, 1000);
        });

		$('.grid .tools .collapse, .grid .tools .expand').on('click', function () {
            var el = jQuery(this).parents(".grid").children(".grid-body");
            if (jQuery(this).hasClass("collapse")) {
                jQuery(this).removeClass("collapse").addClass("expand");
                el.slideUp(200);
            } else {
                jQuery(this).removeClass("expand").addClass("collapse");
                el.slideDown(200);
            }
        });

		$('.user-info .collapse').on('click', function () {
            jQuery(this).parents(".user-info ").slideToggle();
		});
//***********************************END Grids*****************************
		var handleSidenarAndContentHeight = function () {
        var content = $('.page-content');
        var sidebar = $('.page-sidebar');

        if (!content.attr("data-height")) {
            content.attr("data-height", content.height());
        }

        if (sidebar.height() > content.height()) {
            content.css("min-height", sidebar.height() + 120);
        } else {
            content.css("min-height", content.attr("data-height"));
        }
    }
	$('.panel-group').on('hidden.bs.collapse', function (e) {
	  $(this).find('.panel-heading').not($(e.target)).addClass('collapsed');
	})

	$('.panel-group').on('shown.bs.collapse', function (e) {
	 // $(e.target).prev('.accordion-heading').find('.accordion-toggle').removeClass('collapsed');
	})

//***********************************BEGIN Layout Readjust *****************************

	//Break point entry
	$(window).bind('enterBreakpoint320',function() {
		$('#main-menu-toggle-wrapper').show();
		$('#portrait-chat-toggler').show();
		$('#header_inbox_bar').hide();
		$('#main-menu').removeClass('mini');
		$('.page-content').removeClass('condensed');
		rebuildSider();
	});

	$(window).bind('enterBreakpoint480',function() {
		$('#main-menu-toggle-wrapper').show();
		$('.header-seperation').show();
		$('#portrait-chat-toggler').show();
		$('#header_inbox_bar').hide();
		//Incase if condensed layout is applied
		$('#main-menu').removeClass('mini');
		$('.page-content').removeClass('condensed');
		rebuildSider();
	});

	$(window).bind('enterBreakpoint768',function() {
		$('#main-menu-toggle-wrapper').show();
		$('#portrait-chat-toggler').show();

		$('#header_inbox_bar').hide();
		if( /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ) {
			$('#main-menu').removeClass('mini');
			$('.page-content').removeClass('condensed');
			rebuildSider();
		}
	});

	$(window).bind('exitBreakpoint320',function() {
		$('#main-menu-toggle-wrapper').hide();
		$('#portrait-chat-toggler').hide();
		$('#header_inbox_bar').show();
		closeAndRestSider();
	});

	$(window).bind('exitBreakpoint480',function() {
		$('#main-menu-toggle-wrapper').hide();
		$('#portrait-chat-toggler').hide();
		$('#header_inbox_bar').show();
		closeAndRestSider();
	});

	$(window).bind('exitBreakpoint768',function() {
		$('#main-menu-toggle-wrapper').hide();
		$('#portrait-chat-toggler').hide();
		$('#header_inbox_bar').show();
		closeAndRestSider();
	});
//***********************************END Layout Readjust *****************************

//***********************************BEGIN Function calls *****************************
	function closeAndRestSider(){
	  if($('#main-menu').attr('data-inner-menu')=='1'){
		$('#main-menu').addClass("mini");
		$.sidr('close', 'main-menu');
		$.sidr('close', 'sidr');
		$('#main-menu').removeClass("sidr");
		$('#main-menu').removeClass("left");
	  }
	  else{
		$.sidr('close', 'main-menu');
		$.sidr('close', 'sidr');
		$('#main-menu').removeClass("sidr");
		$('#main-menu').removeClass("left");
	}

	}
	function rebuildSider(){
		$('#main-menu-toggle').sidr({
				name : 'main-menu',
				side: 'left'
		});
	}
//***********************************END Function calls *****************************

//***********************************BEGIN Main Menu Toggle *****************************
	$('#layout-condensed-toggle').click(function(){
		$.sidr('close', 'sidr');
		if($('#main-menu').attr('data-inner-menu')=='1'){
			//Do nothing
		}else{
			if($('#main-menu').hasClass('mini')){
				$('#main-menu-wrapper ul li').removeClass('.message-tooltip');
				$('#main-menu').removeClass('mini');
				$('.page-content').removeClass('condensed');
				$('.scrollup').removeClass('to-edge');
				$('.header-seperation').show();
				$('.header-seperation-small').hide();
				//Bug fix - In high resolution screen it leaves a white margin
				$('.header-seperation').css('height','61px');
				$('.footer-widget').show();
				$.cookie('mini', "false",{path: '/'});
			} else{
				$('#main-menu').addClass('mini');
				$('#main-menu-wrapper ul li').addClass('.message-tooltip');
				$('#main-menu-wrapper ul li').tooltip('toggle');
				$('#main-menu-wrapper ul li').tooltip('hide');
				$('.page-content').addClass('condensed');
				$('.scrollup').addClass('to-edge');
				$('.header-seperation').hide();
				$('.header-seperation-small').show();
				$('.footer-widget').hide();
				$.cookie('mini', "true",{path: '/'});
			}
			//修复左侧主菜单展开收起时样式问题
			var width = $('#main-menu').css("width") ;
			$(".slimScrollDiv").css({"width":width});
			$("#main-menu-wrapper").css({"width":width});
		}
	     $('.page-sidebar > ul > li').tooltip('hide');
	});

//********快捷菜单的弹出****************//
	$('#quick-menu').click(function(){
		$('.newMenu').animate({top: "0px"});
		 return false;
	});
	//newMenu点击其他地方不显示
	$('.newMenu').hover(function(event) {
			$(".newMenu").unbind('mousedown');
		},function(){
			$('html').one('click',function() {
				$('.newMenu').css('top','-106px');
			});
			event.stopPropagation();
		});
//标题说明
	$('.title-question').click(function(){
		$('.title-content').fadeToggle({top:"0px"});
		 return false;
	});
//左侧菜单滚动条显示
	$(window).resize(function () {
		$('[data-aspect-ratio="true"]').each(function () {
			$(this).height($(this).width());
		});
		$('[data-sync-height="true"]').each(function () {
			equalHeight($(this).children());
		});
		if (!(/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent))) {
			$('#main-menu-wrapper').slimScroll({resize: true});
		}
	});
	
//*********换肤设置****************************//
//***** 顶部************//

	$('.header-tooltip').tooltip('toggle');
	$('.message-tooltip').tooltip('toggle');
	$('.message-tooltip').tooltip('hide');
	$('.header-tooltip').tooltip('hide');

	$('#message-white').click(function(){
		$('.header').css("backgroundColor","#fff");
		$('.page-sidebar-wrapper').css("backgroundColor","#1b1e24");
	});
	
	$("#colors-options-id").on("click","#header-white", _setCustomStyle("white") );
	$("#colors-options-id").on("click","#header-blue",  _setCustomStyle("blue") );
	$("#colors-options-id").on("click","#header-green", _setCustomStyle("green") );
	$("#colors-options-id").on("click","#header-red",   _setCustomStyle("red") );
	$("#colors-options-id").on("click","#header-orange",_setCustomStyle("orange") );

	var username = $.cookie('login_user');
	function setStyleCookie(style){
		if(style == undefined || style == ""){
			$.cookie('color_option_' + username , 'white');
		}else{
			$.cookie('color_option_'+ username , style ,{ expires:7 ,path:'/'} );
		}
	}
	
	function setCustomStyle(style){
			if(style == null){
				style = "white" ;
			}
			if(style == 'orange'){
				$('.header').css("backgroundColor","#ff5f3b");
				$('.page-sidebar-wrapper').css("backgroundColor","#333");
			}else if (style == 'white'){
				$('.header').removeAttr("style");
				$('.page-sidebar-wrapper').removeAttr("style");
			}else if (style == 'blue'){
				$('.header').css("backgroundColor","#4cacff");
				$('.page-sidebar-wrapper').css("backgroundColor","#1d2436");
			}else if (style == 'green'){
				$('.header').css("backgroundColor","#6db131");
				$('.page-sidebar-wrapper').css("backgroundColor","#1c2118");
			}else if (style == 'red'){
				$('.header').css("backgroundColor","#f83e4c");
				$('.page-sidebar-wrapper').css("backgroundColor","#0d1e2b");
			}
			setStyleCookie(style);
	}
	
	function _setCustomStyle(style){
		return function(){
			setCustomStyle(style);
		}
	}
	
	//cookie 每次访问都会被刷新到7天，所以除非7天不登陆，不会出现丢失的情况。7天不登陆系统是否强制要求登陆？
	//以后可以加上将访问风格设置到数据库的办法。
	var userSetStyle = $.cookie('color_option_' + username );
	if( userSetStyle != undefined && userSetStyle != null ){
		setCustomStyle( userSetStyle );
	}
	
	
	
//*********左侧菜单****************//
//***********************************END Main Menu Toggle *****************************

//***********************************BEGIN Slimscroller *****************************
	$('.scroller').each(function () {
        $(this).slimScroll({
                size: '7px',
                color: '#a1b2bd',
                height: $(this).attr("data-height"),
                alwaysVisible: ($(this).attr("data-always-visible") == "1" ? true : false),
                railVisible: ($(this).attr("data-rail-visible") == "1" ? true : false),
                disableFadeOut: true
        });
    });
//***********************************END Slimscroller *****************************


//***********************************BEGIN Global sparkline chart  *****************************
	if ($.fn.sparkline) {
		$('.sparklines').sparkline('html', { enableTagOptions: true });
	}
//***********************************END Global sparkline chart  *****************************

//***********************************BEGIN Function calls *****************************
	 $('table th .checkall').on('click', function () {//这里可能挪到list.js 了，以后可以注释掉
		 var $this=$(this);
			if($this.is(':checked')){
				 $this.closest('table').find("tbody").find(':checkbox').each(function(){//用下面注释的方式不能用  可能哪有冲突  只有用click来代替
					 var $this=$(this);
					 if(!$this.is(':checked')){
						 $this.attr('checked', true).parents("tr").addClass('row_selected');
					 }
				 });
			}else{
				$this.closest('table').find("tbody").find(':checkbox').attr('checked', false).parents("tr").removeClass('row_selected');
			}
    });
	  /*  飞哥说先不要这个效果
	 $(document).on('click','.one-row-selected input[type="checkbox"]', function () {
		 var $this=$(this);
		 if($this.is(':checked')){
			 $this.closest('tr').siblings().find(':checkbox').each(function(){
				 if($(this).is(':checked')){
					 $(this).attr('checked', false).closest("tr").removeClass('row_selected');
				 }
			 });
		}
    });
	*/
//***********************************BEGIN Function calls *****************************

//***********************************BEGIN Function calls *****************************
	$('.animate-number').each(function(){
		 $(this).animateNumbers($(this).attr("data-value"), true, parseInt($(this).attr("data-animation-duration")));
	});
	$('.animate-progress-bar').each(function(){
		 $(this).css('width', $(this).attr("data-percentage"));

	})
//***********************************BEGIN Function calls *****************************

//***********************************BEGIN Tiles Controller Options *****************************
//	$(' .reload').click(function () {
//		var el =$(this).parent().parent().parent();
//		blockUI(el);
//		  window.setTimeout(function () {
//               unblockUI(el);
//            }, 1000);
//	});
	$('.controller .remove').click(function () {
		$(this).parent().parent().parent().parent().addClass('animated fadeOut');
		$(this).parent().parent().parent().parent().attr('id', 'id_remove_temp_id');
		 setTimeout( function(){
			$('#id_remove_temp_id').remove();
		 },400);
	});
        if (!jQuery().sortable) {
            return;
        }
        $(".sortable").sortable({
            connectWith: '.sortable',
            iframeFix: false,
            items: 'div.grid',
            opacity: 0.8,
            helper: 'original',
            revert: true,
            forceHelperSize: true,
            placeholder: 'sortable-box-placeholder round-all',
            forcePlaceholderSize: true,
            tolerance: 'pointer'
        });
//***********************************BEGIN Function calls *****************************

	$(window).resize(function() {
		calculateHeight();
		$.sidr('close', 'sidr');
	});

	$(window).scroll(function(){
        if ($(this).scrollTop() > 100) {
            $('.scrollup').fadeIn();
        } else {
            $('.scrollup').fadeOut();
        }
    });
	//增加提交和重置的操作就可以了。所有的form已被统一增加了校验
	$form = $(".validate-form");
	if($form.length > 0 ){
		$form.find("button[type=reset]").on("click",function(evt){
			var validator = $form.validate();
			validator.resetForm();
			resetValidateClass($form);
		});
	}
	
	$('.scrollup').click(function(){
		$("html, body").animate({ scrollTop: 0 }, 700);
		return false;
    });
	
	$(document).on("click" , "button.close[data-dismiss=alert]" ,function(){
		$(this).closest(".alert").remove();
	});
	
	$(document.body).click(function(el){
		clickOutMessageList(el);
		clickOutTaskList(el);
	});
	
	$("form span.top-search").on("click",function(){
		$(this).closest("form").submit();
	})
	
	//$("img").unveil();
	//可搜索的下拉框
	var $select=$(".select2");
	if($select&&$select.length>0){
		$select.select2();
	}

});

//***********************************BEGIN Function calls *****************************
function blockUI(el) {
        $(el).block({
            message: '<div class="loading-animator"></div>',
            css: {
                border: 'none',
                padding: '2px',
                backgroundColor: 'none'
            },
            overlayCSS: {
                backgroundColor: '#fff',
                opacity: 0.3,
                cursor: 'wait'
            }
        });
 }

 // wrapper function to  un-block element(finish loading)
function unblockUI(el) {
    $(el).unblock();
}

function calculateHeight(){
		var contentHeight=parseInt($('.page-content').height());
		if(911 > contentHeight){
		
		}
}

//JSON.stringify({
//acl : {
//	id : aclId
//},
//maps : maps
//})
function find_label(input_element) {
	// try previous element
	prev = input_element.previousElementSibling;
	while (prev != null) {
		if (prev.tagName == "LABEL")
			return $(prev).text().replace(" ", "");
		prev = prev.previousElementSibling;
	}
	// try parent's previous element
	prev = input_element.parentElement.previousElementSibling;
	while (prev != null) {
		if (prev.tagName == "LABEL")
			return $(prev).text().replace(" ", "").replace(":", "").replace("：", "");
		prev = prev.previousElementSibling;
	}
	// return null
	return;
}

//$form表单元素  param:json对象 type:post/get之类 fun:回调函数
function ajaxFunction($form,param,func){
	$.ajax({
		url : param.url,
		type : param.type,
		dataType : "json",
		data : JSON.stringify(param.data),
		contentType : "application/json",
		success : function(result) {
			if(result&&result!=null){
				var error=result.errors;
				if(error&&error!=null){
					var text="出错提示：";
					if (error['message']) {
						text += error['message'];
					}
					text += "<br/>";
					$form.find("div#error-msg").remove();
					$.each(error, function(k,v){
						if (k=="message") {
							return;
						}
						var input_field = $form.find("input[name="+k+"]");
						var input_name = null;
						if (input_field.length > 0) {
							input_field = input_field[0];
							input_name = find_label(input_field);
						}
						if (input_name) {
							text += input_name+": " + v + "<br/>";
						} else {
							text += k+": " + v + "<br/>";
						}
						//label=$('<label for="hostname" class="error">'+v+'</label>');
						//$('<span class="error"></span>').insertAfter(element).append(label)
						//var parent = $(element).parent('.input-validation');
						//parent.removeClass('success-control').addClass('error-control');
					});
					var $error_div = $('<div class="alert alert-error" id="error-msg">'
							+ '<button class="close" data-dismiss="alert"></button><span>'
							+ text + '</span></div>' );
					$form.prepend($error_div);
					$form.find("button[type=submit]").removeAttr("disabled");
					return;
				}
			}
			func(result);
		},
		error : function(jqXHR, textStatus, errorThrown) {
			showAjaxErrorMesage(jqXHR);
		}
	});

}

function showSucessMessage(message){
	//alert(message);//暂时注释掉  以后优化。。。。。。
}

function showErrorMessage(message){
	alert(message);
}

function showAjaxErrorMesage(xhr){
    var message = "访问出错！";

    if(xhr.status == 0 ){
        message += parseHttpResponseCode("0");
    }else  if(xhr.status !="200"){
        var xhr_msg = parseHttpResponseCode(xhr.status);
        message = message +"  " +   xhr.status + "  " + xhr_msg ;
    }
    showErrorMessage(message);
}

//高级设置中的显示和隐藏
function showOrhideForSet($set,$info){
	$set.click(function(){
		$info.fadeToggle();
	});
}


function formValidate($form,rules,message,func){

	 $form.validate({
        focusInvalid: false,
        ignore: "",
        rules: rule[rules],
       errorPlacement: function (label, element) { // render error placement for each input type
			$('<span class="error"></span>').insertAfter(element).append(label)
            var parent = $(element).parent('.input-validation');
            parent.removeClass('success-control').addClass('error-control');
        },

        highlight: function (element) { // hightlight error inputs
			var parent = $(element).parent();
            parent.removeClass('success-control').addClass('error-control');
        },
        success: function (label, element) {
			var parent = $(element).parent('.input-validation');
			parent.removeClass('error-control').addClass('success-control');
        },
		messages: message,
		submitHandler:function(form){
            func();
        }
    });
}

function refreshFisrtPage(urlstr,date){
	var url=new String(urlstr);
	if(url.lastIndexOf("#")!=-1){
		url=url.replace(/#/,"");
	}
	if(url.indexOf("_date")!=-1){
		url=url.replace(/_date=([0-9]+)/,"_date="+date.getTime());
	}else {
		if(url.indexOf("?")!=-1){
			url+="&_date="+date.getTime();
		}else{
			url+="?_date="+date.getTime();
		}
	}
	if(url.indexOf("page")!=-1){
		url=url.replace(/page=([0-9]+)/,"page=1");
	}
	location.href=url;
}


function refreshCurrentPage(urlstr,date){
	var url=new String(urlstr);
	if(url.lastIndexOf("#")!=-1){
		url=url.replace(/#/,"");
	}
	if(url.indexOf("_date")!=-1){
		url=url.replace(/_date=([0-9]+)/,"_date="+date.getTime());
	}else {
		if(url.indexOf("?")!=-1){
			url+="&_date="+date.getTime();
		}else{
			url+="?_date="+date.getTime();
		}
	}
	location.href=url;
}
function formToJson($form){
	var json={};
	$form.find("[name]").each(function(){
		var name=$(this).attr("name");
		var value=$(this).val();
		json[name]=value;
	});
	return json;
}


function addValidateClass(){//给form表单input的div添加验证样式
	$("form input[name]").each(function(){
		var obj=$(this).parent();
		if(!obj.hasClass("input-validation")){
			obj.addClass("right").addClass("input-validation");
		}
	});
}

function resetValidateClass($form){//form表单input的div删除验证样式
	$form.find("input[name]").each(function(){
		var obj=$(this).parent();
		obj.removeClass('error-control').removeClass('success-control');
	});
}

$.fn.extend({
		toJson:function(){ //这种方式还没有考虑到单选框的问题！
			if($(this).is("form")||$(this).is("div")){
			   var json={};
			   $(this).find("input:enabled[name]").each(function(){
				   if( this.name ){
					  	var name=this.name;
						var value=this.value;
						json[name]=value;
					}
				});
			   
			   $(this).find("textarea").each(function(){
				   if( this.name ){
					  	var name=this.name;
						var value=this.value;
						json[name]=value;
					}
				});
			   
			   $(this).find('input[type="checkbox"]').each(function(){
					if(this.name && this.checked){
						var name=this.name;
						var value="on";
						json[name]=value;
					}else if(this.name && !this.checked){
						var name=this.name;
						var value="off";
						json[name]=value;
					}
			   });
			   $(this).find(':radio:checked[name]').each(function(){
						var name= this.name ;
						var value=this.value;
						json[name]=value;
			   });
			   
			    $(this).find('select:enabled[name]').each(function(){
				   var name=this.name;
				   json[name] = $(this).val();
				});
			   return json;
		   }else{
			   //alert("不是div或者form元素");
		   }
	    } ,

	    closeModal:function(){
	    	if($(this).is("div")&&$(this).hasClass("modal")){
	    		$(this).find("[data-dismiss]")[0].click();
	    	}

	    },

	    _validate:function( rule_name ){
	    	if($(this).is("form")){
	    	return	$(this).validate({
	    	        focusInvalid: false,
	    	        ignore: "",
	    	        rules: global_rule[rule_name],
	    	        errorPlacement: function (label, element) { // render error placement for each input type
	    				$('<span class="error"></span>').insertAfter(element).append(label)
	    	            var parent = $(element).parent('.input-validation');
	    	            parent.removeClass('success-control').addClass('error-control');
	    	        },

	    	        highlight: function (element) { // hightlight error inputs
	    				var parent = $(element).parent();
	    	            parent.removeClass('success-control').addClass('error-control');
	    	        },
	    	        success: function (label, element) {
	    				var parent = $(element).parent('.input-validation');
	    				parent.removeClass('error-control').addClass('success-control');
	    	        },
	    			messages: global_message[rule_name]

	    	    });
	    	}else{
	    		// alert("不是div或者form元素");
	    		 return null;
	    	}
	    },
	    
	    //对表单进行重置，同时删除前端验证产生的校验信息。
	    resetform:function(){
	    	if($(this).is("form")){
	    		$(this)[0].reset();
	    		$(this).validate().resetForm();
	    		resetValidateClass($(this));
	    	}
	    }
	    //如果需要对单个输入框进行重置，还需另外写实现
});

function createDynamicDivAjax(url,ruletemp,fresh_num,func){//从后台生成div的  func回调函数  fresh_num 0刷新当前页  1刷新到第一页
		if(!url || url=="undefined"){
			return;
		}

		if(!ruletemp){
			ruletemp="noRule";
		}
		$containerDiv = $("#_new") ;
		if( $containerDiv.length == 0 ){//没有这个div 就新建一个  用来装后台返回来的div
			$containerDiv = $("<div id='_new'></div>");
		}else{
			$containerDiv.detach();
		}
		$containerDiv.html("");
		var date1=new Date();
		$containerDiv.load( urlAddPara(url,date1.getTime()) ,function(response, status, xhr){
			if(xhr.status !="200"){
                showAjaxErrorMesage(xhr);
				return ;
			}
			var $modalDiv=$containerDiv.find( "div:eq(0)" );
			var $form= $containerDiv.find("form") ;
			if($form){
				addValidateClass();//给form表单input的div添加样式
				$form._validate( ruletemp );
				$modalDiv.modal("show");
				if($("#_new .advanceSettingInfo-1")){
					$("#_new .advanceSettingInfo-1").hide();
					showOrhideForSet($("#_new .advanceSetting-1"),$("#_new .advanceSettingInfo-1"));
				}

				$form.find("button[type=submit]").click(function(evt){
					evt.preventDefault();
					var date=new Date();
					$form.find("button[type=submit]").attr("disabled","disabled");//防止重复提交
					if($form.valid()){
					    var _data=$form.toJson();
						var param={
								type:$form.attr("method"),
								url:$form.attr("action"),
								data:_data
						};
						ajaxFunction($form,param,function(data){//回调函数
							$modalDiv.closeModal();
							if(func && typeof(func) == "function"){
								func();
							}
							if(fresh_num==0){
								refreshCurrentPage(location,date);
							}else if(fresh_num==1){
								refreshFisrtPage(location,date);
							}
							//$(".reload").click();
						});
					}else{
						$form.find("button[type=submit]").removeAttr("disabled");
					}
				});
				
				$form.find("button[type=reset]").click(function(evt){
					$form.resetform();
				});
			}
		});
		
		$(".page-container").after( $containerDiv );

}



function showAjaxModal(){//显示动态生成的弹出框
		//给“更多”等操作弹出的菜单根据上级li样式绑定事件
	 	$(".btn-group .dropdown-menu a[data-url]").off("click").on("click",function(evt){
	 		evt.preventDefault();
	 		if($(this).parent().hasClass("disabled")){
				return;
			}
			var id= $("input[type=checkbox]:checked").val();
			var url= new String($(this).attr("data-url")).replace(/{id}/, id);
			var rule=$(this).attr("data-rule");
			createDynamicDivAjax(url,rule,0);//0刷新当前页1 刷新到第一页
		 });
	    
	 	$("button[data-url]:not(.reload)").unbind("click").click(function(){
	 		
	 		var obj= $("input[type=checkbox][name!=switch]:checked");
	 		var id="";
	 		if(obj.length>0){
	 			id=obj.val();
	 		}
			var url= new String($(this).attr("data-url")).replace(/{id}/, id);
			var rule=$(this).attr("data-rule");
			createDynamicDivAjax(url,rule,0);//0刷新当前页1 刷新到第一页
		 });

	 	$(".rightMenu a[data-url]").unbind("click").click(function(){
	 		$(".rightMenu").hide();
	 		if($(this).parent().hasClass("disabled")){
				return;
			}
	 		var str=$(".rightMenu").attr("name");
			str=new String(str);
			var id=""
			if(str!=null){
				var obj=str.split("$_&");
				if(obj.length>0){
					id=obj[0];
				}
				var url= new String($(this).attr("data-url")).replace(/{id}/, id);
				var rule=$(this).attr("data-rule");
				createDynamicDivAjax(url,rule,0);//0刷新当前页1 刷新到第一页
			}

		 });

		 $("table tr.show-others").off("dblclick").on("dblclick", "td:not(':first-child')", function(e){//列表页中 tr双击事件
			 var $tr = $(this).closest("tr");
			 var task_status = $tr.find("td[name=task_status]").hasClass("text-success");
			 if ( task_status ) {
				//正在任务中
				 return ;
			 } else {
				 //其他状态，失败，还原，或者没有任务
			 }
			 var id=$(this).parent().find("input[type=checkbox]").val();
			 var url=new String($(".dropdown-menu a[name*=update]").attr("data-url")).replace(/{id}/, id);
			 var rule=$(".dropdown-menu a[name*=update]").attr("data-rule");
			 
			 createDynamicDivAjax(url,rule,0);//0刷新当前页1 刷新到第一页
	      });
		 
		 //让列表的翻页带上列表所用的搜索条件
		 var $as = $("div[name=listtable] > .nextpage > ul.pagination li:not(.disabled) a");
		 $as.each(function(){
			 $(this).click(function(evt){
					evt.preventDefault();
					var page_url = this.href;
					var search_word = $(".grid-title form input[name='search']").val();
					if(search_word){
						page_url += "&search="+search_word ;
					}
					location.href = page_url ;
				});
		 });
}


function createTabEvent(){//对于多个tab弹出框如 用户管理新建
	
	$(".tab-content").on("click",".previous_tab",function(e){
		$(".nav li.active").prev().find("a").click();
	});
	
	$(".tab-content").on("click",".next_tab",function(e){
		if( IsValidated( $(this).closest(".tab-pane") ) ){
			$(".nav li.active").next().find("a").click();
		}else{

		}
	});
	
	$(".last_tab").on("click",function(){
		var form=$(this).parents("form");
		if(!form.valid()){
			$(".tab-pane.active").removeClass("active");
			var name=$(".error-control:first").parents(".tab-pane").attr("id");
			$("a[name=#"+name+"]").parent()[0].classList.remove("active");
			$("a[name=#"+name+"]").click();
		}
	});
	
	$("._tab_ul li a").on("click",function(evt){
		evt.preventDefault();
		var s=$(this).attr("name");
		$(".tab-pane.active").removeClass("active");
		$(s).addClass("active");
	});
	
}

//有checkbox列表的菜单/按钮根据表格选定行,弹出页面上已指定的隐藏div对话框
function createMenuForCheck(obj1){
	obj1.off("click").on("click",function(evt){
		evt.preventDefault();
		if($(this).parents("li").hasClass("disabled")){
			return;
		}
		var $target=$( $(this).attr("name") );
		
		if( $target.length > 0 ){
			var obj=$("tbody input[type=checkbox]:checked");
			var id= obj.val();
			var _name=obj.parents("tr").find("td:eq(1)").text();
			showLocalMenu(id, _name, $target[0]);			
		}
	});
}

//展示一个弹出框
function showLocalMenu(id , resource_name ,target){
	if( target ){
		$target = $(target );
		$target.find("input[name=id]").val("");
		var $form = $target.find("form") ;
		$form.resetform();
		$target.find(" .modal-header span").html( resource_name );
		
		//确认取消这种提示框内部的资源名
		var _name = "<b>"+ resource_name + "</b>" ;
		$target.find(".resource-name").html(_name);
		
		$target.find("input[name=id]").val( id );
		$form.find("button[type=submit]").removeAttr("disabled");
		 
		var url=new String( $form.attr("action"));
		var old_url_input=$target.find("input._actionurl");
		if(old_url_input.length>0){
			url=old_url_input.val();
		}else{
			$target.append("<input type='hidden' class='_actionurl' value="+url+" />"); 
		}
		url=url.replace(/{id}/, id );
		$form.attr("action",url);
		
		$target.modal("show");
			
	}else{
		console.log("请求的modal对象不存在");
	}
}

//右上角显示的那个黑色的后台消息列表
function reFreshMessageList(){
	var div='<div id="gritter-notice-wrapper"></div>';
	var str='<div role="alert" style="display:{display}" class="gritter-item-wrapper growl-success" data-time="{time}" data-status="{status}" id="{id}">'
		+'<div class="gritter-top"></div><div class="gritter-item"><a tabindex="1" href="#" class="gritter-close"><i class="fa fa-times"></i></a><div class="gritter-without-image">'
		+'<span class="gritter-title">{message}</span><p></p></div><div style="clear:both"></div></div><div class="gritter-bottom"></div></div>';
	
	if($("#gritter-notice-wrapper").length<1){
		$("body").append(div);
	}
	var count=0;
	if($("#gritter-notice-wrapper").length>0){
		$.get("/jobs.json?"+new Date().getTime(),{"duration":5},function(data){
			if(data!=null){
				var resourcetype=$("body").attr("data-resourcetype");
				if(data.unfinished_job_count!=0){
					$("a[name=tasklist] span").html(data.unfinished_job_count);//修改数量
				}else{
					$("a[name=tasklist] span").html("");//修改数量
				}
				var endstatus=null;
				var map = {};
				if(data.job_list!=null){
					var tempdata=data.job_list;
					var _id=null;
					var _refreshFlag = false ;
					var arrSucceed = new Array();
					
					for(var i=0; i<tempdata.length;i++){
						var _data=tempdata[i];
						if(_data){
							var id=_data.id,resource_id=_data.resource_id,type=_data.resource_type, status=_data.state,message=_data.display_desc,
								name=_data.resource_name,event_name=_data.flow_name;
							var obj=$("#"+type+"_"+resource_id);
							if(message == null ){
			    				message = "请稍候...";
			    			}
							if(obj&&obj.length<1){//如果没有就添加
								var s=str.replace(/{id}/, type+"_"+resource_id).replace(/{message}/,name+"&nbsp;&nbsp;"+message).replace(/{time}/,
										Date.parse(new Date())).replace(/{status}/, status);
								if(status!="REVERTED"&&status!="FAILURE"&&status!="SUCCESS"){//第一次出现的都是正在进行的任务
									s=s.replace(/{display}/,"block");
									$("#gritter-notice-wrapper").append(s);
								}
							}else{//有就改变message
								var nowtime=Date.parse(new Date());
								var time=parseInt(obj.attr("data-time"));
								if(status=="FAILURE"){
									obj.removeClass("growl-success").addClass("growl-danger");
								}
								obj.find("span").html(name+"&nbsp;&nbsp;"+message);
								if(status!=obj.attr("data-status")){
									//console.log("state changed !!    " +  message);
									obj.attr("data-time",nowtime).attr("data-status",status);
									infoPageRefresh( type , resource_id );
									if(resourcetype==type||type.indexOf(resourcetype)!=-1){
										if(status=="SUCCESS"||status=="FAILURE"){
											var small = $("table.table-info").length;
											if( small > 0   ){
												_refreshFlag = true ;
											}
											arrSucceed.push(resource_id);
										}
									}
								}
								
								if(status=="REVERTED"||status=="FAILURE"||status=="SUCCESS"){
									delayRemove(obj);
								}else{
									var tempstatus=obj.attr("data-status");
									if(tempstatus==status){//如果状态在一定时间(5分钟)内没有改变 说明可能出问题了  这个div隐藏 在当前页面(不跳转或者刷新)以后也不会显示
										if(nowtime-time>=displaytime_error){
											obj.hide();
										}
									}
								}
							}
							$("a.gritter-close").click(function(evt){//添加关闭事件
								evt.preventDefault();
								$(this).parents("div[role=alert]").remove();
							});
							if(resourcetype==type||type.indexOf(resourcetype)!=-1){
								map[resource_id]=status;
							}
						}
		    		}
					
					if ( _refreshFlag ){
						$(".reload").click();
						//console.log("inner pages 已请求刷新");
					}
					
					var id_in_page = $("div[name=listtable] table tr td input").map(function(){
						return this.value;
					}).get();
					
					if(arrayCrossed(id_in_page , arrSucceed )){
						reload($(":button.reload "));
					}else{
						$.each(map,function(key,val){
							var obj=$("tbody:first tr input[value="+key+"]");
							var $status_td = obj.parents("tr").find("td[name='task_status']") ;
							var s=$status_td.text();
							
							if(s!=null){
								s=s.replace(/(^\s*)|(\s*$)/g,"");
							}
							//以前状态不是"" 但是当前返回状态是"" 就更新msg==""&&s!=""
							var $div=$("#"+resourcetype+"_"+key);
							var msg = statusToMsg( val ) ;
							if(obj.length>0 && msg != s ){//状态不一样，更新任务状态
								$status_td.text(msg);
								if(msg.length > 0 ){
									$status_td.addClass('text-success');
								}
							}
							
						}); 
					
					}
					
					
				}
				
			}
		},"json");
	}

}

function delayRemove(obj){
	setTimeout(function(){
		obj.remove();
	},displaytime);
}

function statusToMsg(status){
	var msg="";
	if(status=="SUCCESS"){
		msg="";
	}else if(status=="FAILURE"||status=="REVERTED"){
		msg="";
	}else if(status=="RUNNING"){
		msg="任务中";
	}else if(status=="PENDING"){
		msg="等待中";
	}
	return $.trim(msg) ;
}

//如果详情页外部状态有更新，刷新整个页面 
function infoPageRefresh(resourceType , resourceId){
	if( !resourceType || !resourceId ){
		return ;
	}
	var page_resourceType = $("body").attr("data-resourcetype");
	var page_resourceId   =	$("table.table-info tbody tr td:contains('ID') ~ td").html() ;
	
	if( !page_resourceId ) { return ; }
	
	if( page_resourceType == resourceType  && page_resourceId == resourceId ) {
		refreshCurrentPage(location,new Date());
	}
}


function refreshTaskListDiv(){//生成正在进行的任务列表
	var num=0;
	var title='<li><label for="demo-header-variations" class="control-label bold inline m-l-20">您有 {num} 个正在进行的任务</label></span> </li>';
	 var tasks='<li class="task"><div class="message-progress"><div class="heading text-success"><a href="{url}" >{name}</a>'
		 	+ '<a href="#" class="pull-right message-times"> </a></div>'
		 	+ '<p class="text-muted no-margin">{message}</p></div></li>';
    $("ul.tasklist").html("");
    $.get("/jobs.json",{"duration":5},function(data){
    	if(data!=null){
    		if(data.unfinished_job_count==0){
    			$("a[name=tasklist] span").html("");
    		}else{
    			$("a[name=tasklist] span").html(data.unfinished_job_count);
    		}
    		title=title.replace(/{num}/,data.unfinished_job_count);
    		
    		var tempdata=data.job_list;
    		for(var i=0;i<tempdata.length;i++){
				var _data=tempdata[i];
    			var id=_data.resource_id,type=_data.resource_type, status=_data.state,message=_data.display_desc,name=_data.resource_name,url=_data.access_url,event_name=_data.flow_name;;
    			if(message == null){
    				message = "";
    			}
    			/*if(status!="REVERTED"&&status!="FAILURE"&&status!="SUCCESS"){
    				if(num<4){
    					if(url==null||url==""){
    						url="###";
    					}
    					if(event_name.indexOf("delete")!=-1){
    						url="###";
    					}
    					title+=tasks.replace(/{message}/,message).replace(/{name}/,name).replace(/{url}/,url);
    				}
    				num++;
    			}*/
    			if(status!="REVERTED"&&status!="FAILURE"&&status!="SUCCESS"){
    				url = "/user/logs/" ;
    				title+=tasks.replace(/{message}/,message).replace(/{name}/,name).replace(/{url}/,url);
    			}
    		}
    		//$("ul.tasklist").html(title+'<li class="pull-right"><a href="#">查看更多</a></li>');
    		title += '<li class="pull-right"><br/></li> ';
    		$("ul.tasklist").html(title);
    		$(".tasklist .message-times").click(function(evt){
    			evt.preventDefault();
    			$(this).parents("li.task").remove();
    		});
    		
    		
    	}
    },"json");
}

$(function(){
	$("a[name='monitorlist']").click(function(evt){
		evt.preventDefault();
		var obj=$("ul[name=monitorlist]").parents("li");
		var len=$("a[name=monitorlist] span").html();
		if(len==""){
			//return;
		}
		if(obj&&obj.hasClass("open")){
			obj.removeClass("open");
		}else{
			refreshMonitorListDiv();
			obj.addClass("open");
		}
		
	});
	
	$("a#tasklist").click(function(evt){
		evt.preventDefault();
		var obj=$("li[name=tasklist]");
		if(obj&&obj.hasClass("open")){
			obj.removeClass("open");
		}else{
			refreshTaskListDiv();
			obj.addClass("open");
		}
	});

	if($("._new_static").length>0){//如果有此元素才添加 事件
		$("._new_static").click(function(evt){//新建 不从后台生成div的新建
			evt.preventDefault();
			var target=$(this).attr("name");
			$(target).find("button[type=submit]").removeAttr("disabled");
			$(target).find("form").resetform();
			$(target).modal("show");
		});
	}
	
	$(".modal").find("button[type=submit]").click(function(evt){//弹出框表单提交//这段代码的功能是啥子呢
		evt.preventDefault();
		var $form= $(this).parents("form");
		$form.find("button[type=submit]").attr("disabled","disabled");

		var date=new Date();
		var modalid=$form.parents(".fade").attr("id");
		var forwardurl=$("#"+modalid).find("input[name=forwardurl]").val();
		var url=$form.attr("action");
		
		var type=$form.attr("method");
		var data=$form.toJson();
		var param ={
				url:url,
				type:type,
				data:data
			};

		if($form.valid()){
			if(modalid.indexOf("new")!=-1){
				 ajaxFunction($form,param,function(){
					 $("#"+modalid).closeModal();
					 showSucessMessage($("#"+modalid).find("p").text()+"执行成功");
					 if(forwardurl&&forwardurl!=null&&forwardurl!=""){
						 loaction.href=forwardurl;
						 return;
					 }
					 refreshFisrtPage(location,date);
				 });

			}else if(modalid.indexOf("delete")!=-1){
				 ajaxFunction($form,param,function(){
					 $("#"+modalid).closeModal();
					 showSucessMessage($("#"+modalid).find("p").text()+"执行成功");
					 if(forwardurl&&forwardurl!=null&&forwardurl!=""){
						 loaction.href=forwardurl;
						 return;
					 }
					 refreshCurrentPage(location,date);
				 });
			}else {
				 ajaxFunction($form,param,function(){
					 $("#"+modalid).closeModal();
					 showSucessMessage($("#"+modalid).find("h4").text()+"执行成功");
					 if(forwardurl&&forwardurl!=null&&forwardurl!=""){
						 loaction.href=forwardurl;
						 return;
					 }else{
						 refreshCurrentPage(location,date);
					 }
				 });
			}
		}else{
			 $form.find("button[type=submit]").removeAttr("disabled");
		}

	 });
	addValidateClass();

	$("form").each(function(){//给每个加了校验规则的form加校验
		var ruletemp=$(this).attr("data-rule");
		if(ruletemp){
			 $(this)._validate(ruletemp);
		}
	});
});

//在指定位置打印一个提示消息，在mtime时间后隐藏(将扩展为5种风格的提示)
function showMessage(target ,message,mtime,messageType){
	 if(mtime == undefined ){
		 //mtime = 5000 ;
	 };
	 if(messageType == undefined){
		 messageType = 'success' ;
	 }
	 var html = {
			 success: '<div class="alert alert-success alertMsg">'
	 		+'<button class="close" data-dismiss="alert"></button><span>' 
	 		+ message + '</span></div>'  ,
	 		warning : '<div class="alert alertMsg"> <button class="close" data-dismiss="alert"></button> '
	 			+ message + '</div> ' ,
	 		info : '<div class="alert alert-info alertMsg"><button class="close" data-dismiss="alert"></button>'
	 			+ message + '</div>' ,
	 		error : '<div class="alert alert-error alertMsg"><button class="close" data-dismiss="alert"></button>'
	 				+ message + '</div>'
	 };
	 if(messageType == "success"){
		 var msg_div = $( html.success );
	 }else if(messageType == "warning"){
		 msg_div = $( html.warning );
	 }else if(messageType == "info"){
		 msg_div = $( html.info );
	 }else if(messageType == "error"){
		 msg_div = $( html.error );
	 }
	 
	 $(target).append(msg_div);
	 if( mtime  ){
		 setTimeout(_removeMessage(msg_div),mtime ); 
	 }
}
function removeOldMessage(msg_div){
	$(".alertMsg").remove();
}

function _removeMessage(msg_div){
	 return function(){
		 removeOldMessage(msg_div)
	 }
}
//点击在消息列表之外时隐藏消息列表
function clickOutMessageList(el){
	 var thisObj = el.target?el.target:event.srcElement;
	 
	 if($(thisObj).closest("ul[name=monitorlist]").length > 0 ||
			 $(thisObj).closest("#monitorlist").length > 0 ){
		 return ;
	 }	 else {
		 $("div.pull-right ul[name=monitorlist]").parents("li").removeClass("open");;
	 }
	/* do{
		 if(thisObj.id == "lightmenu") return;
		 if(thisObj.tagName == "BODY"){
	   //hidemenu();
			 return;
		 };
	  thisObj = thisObj.parentNode;
	 }while(thisObj.parentNode);*/
}

function clickOutTaskList(el){
	 var thisObj = el.target?el.target:event.srcElement;
	 
	 if($(thisObj).closest("ul.tasklist").length > 0 ||
			 $(thisObj).closest("div.pull-right li[name=tasklist]").length > 0 ){
		 return ;
	 }	 else {
		 $("div.pull-right li[name=tasklist]").removeClass("open");
	 }
}



//分组的validate 的判断。
function IsValidated(group) {
	var isValid = true;
	group.find(':input').each(function (i, item) {
	if (!$(item).valid())
		isValid = false;
	});
	return isValid;
}

function setMultiSelect( $target , header ){
	if(!header ){
		return false ;
	}
	$target.multiSelect({
		selectableHeader: header.selectableHeader,
		selectionHeader: header.selectionHeader,
		selectableOptgroup: true ,
		afterInit: function(ms){
		    var that = this,
		        $selectableSearch = that.$selectableUl.prev(),
		        $selectionSearch = that.$selectionUl.prev(),
		        selectableSearchString = '#'+that.$container.attr('id')+' .ms-elem-selectable:not(.ms-selected)',
		        selectionSearchString = '#'+that.$container.attr('id')+' .ms-elem-selection.ms-selected';
				
		    that.qs1 = $selectableSearch.quicksearch(selectableSearchString);

		    that.qs2 = $selectionSearch.quicksearch(selectionSearchString);
		    
		},
		afterSelect: function(values){
			$target.find('option').each(function(){
                if($(this).val() == values[0]){
                    $(this).attr("selected", true);
                }
            });
            this.qs1.cache();
            this.qs2.cache();
		},
		afterDeselect: function(values){
			$target.find('option').each(function(){
                if($(this).val() == values[0]){
                    $(this).attr("selected", false );
                }
            });
            this.qs1.cache();
            this.qs2.cache();
		}
	});
}

function reload( btn ) {//按钮刷新
	var reloadbutton_url= btn.attr("data-url");
	if(!reloadbutton_url){
		return;
	}
	var el =  $(this).parents(".grid");
    blockUI(el);
	window.setTimeout(function () {
       unblockUI(el);
    }, 1000);
		
	var $o =$("ul.pagination a.active");
	if( $o.length>0){
		var s=new String( $o.attr("href") );
		if(s.indexOf("segment")==-1){
			reloadbutton_url=s+"&segment=true&"+new Date().getTime();
		}
		var search_word = $("form input[name='search']").val();
		if(search_word){
			reloadbutton_url += "&search="+search_word ;
		}
	}
	
	$.get(reloadbutton_url,{},function(data){
		 if(data==null||data==""){
  			 return;
  		 }
		 $("div[name=listtable]").html(data);
		 showAjaxModal();
  		 createMenu();
	},"html");
	
  	$(".others-info").hide();	
}

/***************功能性函数放在下面*********************/

//在url里增加翻页参数，page_url形如 page=3 
function urlAddPagePara(url , page_url){
	if(page_url){
		if(url.indexOf("page")!=-1){
			url = url.replace(/page=([0-9]+)/,  page_url );
		}else{
			url = url + "&" + page_url;
		}
	}
	return url ;
}

function urlAddPara(url , params){
	if(url){
		if(url.indexOf("?")>0){
			return url + "&"+params;
		}else{
			return url + "?"+params;
		}
	}
}

var HTTP_CODES = {
		"200":"成功",
		"404":"请求的网页不存在。",
		"500":"服务器内部错误。",
		"0"	 : "服务器未响应",
		"403":"没有权限访问。",
		"405":"禁用请求中指定的方法。",
		"400":"错误请求! 服务器不理解请求的语法。",
		"401":"未授权!请求要求身份验证。",
		"405":"禁用请求中指定的方法。",
		"406":"无法使用请求的内容特性响应请求的网页。",
		"407":"需要代理授权。",
		"408":"请求超时。",
		"409":"服务器在完成请求时发生冲突。",
		"410":"请求的资源已永久删除。",
		"411":"需要有效长度。",
		"412":"未满足前提条件。",
		"413":"请求实体过大。",
		"414":"请求的 URI 过长，服务器无法处理。",
		"415":"请求的格式不受请求页面的支持。",
		"416":"请求范围不符合要求。",
		"417":"未满足期望值。",
		"501":"尚未实施。",
		"502":"错误网关。",
		"503":"服务不可用。",
		"504":"网关超时。",
		"505":"HTTP 版本不受支持。",
		"300":"多种选择, 针对请求，服务器可执行多种操作。",
		"301":"请求的网页已永久移动到新位置。",
		"302":"服务器目前从不同位置的网页响应请求。",
		"303":"查看其他位置。",
		"304":"请求的网页未修改过。",
		"305":"请求者只能使用代理访问请求的网页。",
		"307":"临时重定向。",
		"201":"已创建。",
		"202":"已接受。",
		"203":"非授权信息。",
		"204":"无内容。",
		"205":"重置内容。",
		"206":"部分内容。"
}

function parseHttpResponseCode(code){
	if(!code){
		return ;
	}
	var desc = HTTP_CODES[code] ;
	if(!desc){
		desc = "默认描述";
	}
	
	var str ;
	str = code + " " + desc ;
	//for (var key in codes){    console.log(key +" " + codes[key]);  }
	return desc;
}

//判断两个 Array 是否包含相同元素
function arrayCrossed(arr , brr ){
	if(arr.length == 0 || brr.length == 0 ){
		return false ;
	}
	for( var i = 0 ; i < arr.length ; i++){
		for( var j = 0; j < brr ;j++){
			if( arr[i] == brr[j] ){
				return true ;
			}
		}
	}
	return false ;
}

//按照英文一个，中文2个的宽度计算字符串长度,结果为字符串所占字符宽度
function getStringLength(obj){
	var length=0;
	for(var i=0;i<obj.length;i++){
		if(fnCheckChineseChar(obj.charAt(i))){					
			length +=2;
		}else{
			length++;
		}
  	}
	return length;
}

function fnCheckChineseChar(obj){
	var reg =/^[\u0391-\uFFE5]+$/;
	return reg.test(obj);
}

//获取前n个显示宽度内的字符串,如果n是奇数，那么取(n+1)/2个字符
function getPreString(str , num ){
	if(str.length == getStringLength(str) ){
		return str.slice(0,num);
	}
	var pointor = 0 ;
	for(var i=0;i<num;i++){
		if( fnCheckChineseChar(str.charAt(i)) ){
			i++;
		}else{
		}
		pointor ++ ;
	}
	return str.slice(0,pointor) ;
}