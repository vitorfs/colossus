$(function () {
    // #notifications defined on base.html template
    var $notifications = $("#notifications");
    var $body = $("body");

    $notifications.on("show.bs.popover", function () {
        var url = $notifications.data("url");
        $.ajax({
            url: url,
            dataType: 'json',
            beforeSend: function () {

            },
            success: function (data) {
                var id = $notifications.attr("aria-describedby");
                $("#" + id + " .popover-body").html(data.html);
                $(".has-notifications", $notifications).removeClass("active");
                $(".empty-notifications", $notifications).addClass("active");
            },
            complete: function () {

            }
        });
    });

    $body.on("click", ".js-mark-all-as-read", function () {
        var url = $(this).data("url");
        $.ajax({
            url: url,
            type: 'post',
            dataType: 'json',
            success: function (data) {
                var id = $notifications.attr("aria-describedby");
                var $notificationBody = $("#" + id + " .popover-body");
                $notificationBody.html(data.html);
            }
        });
    });

    $body.on("click", ".js-clear-all", function () {
        var url = $(this).data("url");
        $.ajax({
            url: url,
            type: 'post',
            dataType: 'json',
            success: function (data) {
                var id = $notifications.attr("aria-describedby");
                var $notificationBody = $("#" + id + " .popover-body");
                $notificationBody.html(data.html);
            }
        });
    });

    $notifications.popover({
      container: '#notificationsContainer',
      html: true,
      placement: 'bottom',
      content: function () {
          var loadingText = $notifications.data("loading");
          return "<div class='py-3 text-center text-muted font-italic' style='width:300px;'>" + loadingText + "</div>";
      }
    });

});
