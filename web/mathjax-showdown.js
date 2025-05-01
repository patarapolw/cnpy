/**
 * @see https://stackoverflow.com/questions/23223718/failed-to-execute-btoa-on-window-the-string-to-be-encoded-contains-characte
 * @see https://stackoverflow.com/a/75155959/9023855
 */
function btoa_utf8(value) {
  return btoa(
    String.fromCharCode(
      // @ts-ignore
      ...new TextEncoder("utf-8").encode(value)
    )
  );
}
function atob_utf8(value) {
  const value_latin1 = atob(value);
  return new TextDecoder("utf-8").decode(
    Uint8Array.from({ length: value_latin1.length }, (element, index) =>
      value_latin1.charCodeAt(index)
    )
  );
}

/** @see https://github.com/easyhappy/math-extension */
var escapehtml = function (str) {
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
};

/**
 * Inline MathJax
 *
 *   We use the constant \(\pi\) to compute the area of a circle.
 *
 * Display MathJax
 *
 *   Here is a multi-line equation:
 *
 *   \[
 *    \begin{align}
 *    \dot{x} & = \sigma(y-x) \\
 *    \dot{y} & = \rho x - y - xz \\
 *    \dot{z} & = -\beta z + xy
 *    \end{align}
 *   \]
 *
 * Dont forget to include
 *
 *	<script type="text/javascript"
 * 	src="http://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-MML-AM_HTMLorMML">
 * </script>
 *
 * @see https://github.com/easyhappy/math-extension
 */
export const mathjaxExtension = function () {
  return [
    {
      type: "lang",
      filter: function (text) {
        // cannot use two 'lang' filters because they break each other.
        return text.replace(/\\\((.*?)\\\)/g, function (match, p1) {
          return (
            "<mathxxxjax>" +
            btoa_utf8("\\(" + escapehtml(p1) + "\\)") +
            "</mathxxxjax>"
          );
        });
      },
    },
    {
      type: "lang",
      filter: function (text) {
        // cannot use two 'lang' filters because they break each other.
        return text.replace(/\\\[([\s\S]*?)\\\]/g, function (match, p1) {
          return (
            "<mathxxxjax>" +
            btoa_utf8("\\[" + escapehtml(p1) + "\\]") +
            "</mathxxxjax>"
          );
        });
      },
    },
    {
      type: "output",
      filter: function (text) {
        // insert data back
        return text.replace(
          /<mathxxxjax>(.*?)<\/mathxxxjax>/g,
          function (match, p1) {
            return atob_utf8(p1);
          }
        );
      },
    },
  ];
};
