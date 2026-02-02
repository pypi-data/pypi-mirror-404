if (!Object.hasOwn) {
    // eslint-disable-next-line no-extend-native
    Object.defineProperty(Object.prototype, 'hasOwn', {
        value: function (object, key) {
            return Object.prototype.hasOwnProperty.call(object, key);
        },
        enumerable: false
    });
}

if (!Object.groupBy) {
    // 旧版本浏览器不支持Object.groupBy方法时，手动实现
    Object.groupBy = function (object, keyFn) {
        return object.reduce((acc, item) => {
            const key = keyFn(item);
            (acc[key] = acc[key] || []).push(item);
            return acc;
        }, {});
    };
}
