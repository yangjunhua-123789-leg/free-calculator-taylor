/* 静态网页版桥接层
 *
 * 桌面版（pywebview）会注入 window.pywebview.api；
 * 纯静态网页没有它，这里补一个同签名的实现，把调用转发到线上 API。
 * 这样 assets/app.js 完全不用改动，前端逻辑与原版保持一致。
 */
(function () {
  "use strict";

  if (window.pywebview && window.pywebview.api) {
    return;
  }

  var BASE = window.__CALC_API_BASE__ || "";

  async function post(path, payload) {
    var response;
    try {
      response = await fetch(BASE + path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
    } catch (error) {
      throw new Error("无法连接计算服务，请检查网络或稍后重试。");
    }
    var data = null;
    try {
      data = await response.json();
    } catch (error) {
      throw new Error("服务端返回了无法解析的响应（HTTP " + response.status + "）。");
    }
    if (!response.ok && (!data || data.error === undefined)) {
      throw new Error("服务端错误（HTTP " + response.status + "）。");
    }
    return data;
  }

  window.pywebview = {
    api: {
      solve_limit: function (expression, center, order, direction) {
        return post("/api/solve", {
          expression: expression,
          center: center,
          max_order: order,
          direction: direction
        });
      },
      plot_range: function (expression, center, lo, hi) {
        return post("/api/plot_range", {
          expression: expression,
          center: center,
          lo: lo,
          hi: hi
        });
      }
    }
  };

  window.dispatchEvent(new Event("pywebviewready"));
})();
