var debug = process.env.NODE_ENV !== "production";
var webpack = require('webpack');
var path = require('path');

module.exports = {
  context: path.join(__dirname, "src"),
  devtool: debug ? "inline-sourcemap" : null,
  entry: path.resolve(__dirname, 'src/js/app.jsx'),
  module: {
    loaders: [
      {
        test: /\.jsx?$/,
        exclude: /(node_modules|bower_components)/,
        loader: 'babel-loader',
        query: {
          presets: ['react', 'env', 'stage-0'],
          plugins: ['react-html-attrs', 'transform-class-properties', 'transform-decorators-legacy'],
        }
      },
      {
        test: /\.css$/,
        exclude: /node_modules/,
          use: [
            {
              loader: 'style-loader',
            },
            {
              loader: 'css-loader',
              options: {
                  importLoaders: 1,
              }
            },
            {
              loader: 'postcss-loader'
            }
          ]
      }
    ]
  },
  resolve: {
    alias: {
      'components': path.resolve(__dirname, 'src/js/components'),
      'styles': path.resolve(__dirname, 'src/stylesheets'),
    },
    extensions: ['.js', '.jsx', '.css']
  },
  output: {
    path: path.resolve(__dirname, "public"),
    filename: "app.min.js"
  },
  plugins: debug ? [] : [
    new webpack.optimize.DedupePlugin(),
    new webpack.optimize.OccurenceOrderPlugin(),
    new webpack.optimize.UglifyJsPlugin({ mangle: false, sourcemap: false }),
  ],
};
