'use strict';

var autoprefixer = require('gulp-autoprefixer');
var browserSync = require('browser-sync').create();
var cache = require('gulp-cached');
var fs = require('fs');
var gulp = require('gulp');
var imagemin = require('gulp-imagemin');
var jscs = require('gulp-jscs');
var jshint = require('gulp-jshint');
var plumber = require('gulp-plumber');
var reload = browserSync.reload;
var rename = require('gulp-rename');
var sass = require('gulp-sass');
var minifyCss = require('gulp-minify-css');
var scsslint = require('gulp-scss-lint');
var sourcemaps = require('gulp-sourcemaps');
var uglify = require('gulp-uglify');
var spawn = require('child_process').spawn;

gulp.task('sass:lint', function() {
  gulp.src('./static/src/sass/*.scss')
    .pipe(plumber())
    .pipe(scsslint());
});

gulp.task('sass:build', function() {
  gulp.src('./static/src/sass/style.scss')
    .pipe(rename({
      suffix: '.min',
    }))
    .pipe(plumber())
    .pipe(sourcemaps.init())
    .pipe(sass({
      // outputStyle: 'compressed',
    }))
    .pipe(autoprefixer())
    .pipe(sourcemaps.write())
    .pipe(gulp.dest('./static/dist/css/'))
    .pipe(reload({
      stream: true,
    }));
});

gulp.task('sass:optimized', function() {
  gulp.src('./static/src/sass/style.scss')
    .pipe(rename({
      suffix: '.min',
    }))
    .pipe(sass({
      outputStyle: 'compressed',
    }))
    .pipe(autoprefixer())
    .pipe(minifyCss({
      compatibility: 'ie8',
    }))
    .pipe(gulp.dest('./static/dist/css/'));
});

gulp.task('sass', ['sass:lint', 'sass:build']);

gulp.task('js:build', function() {
  gulp.src(['./static/src/js/**/*.js'])
    .pipe(plumber())
    .pipe(uglify())
    .pipe(gulp.dest('./static/dist/js'))
    .pipe(reload({
      stream: true,
    }));
});

gulp.task('js:optimized', function() {
  gulp.src(['./static/src/js/**/*.js'])
    .pipe(uglify())
    .pipe(gulp.dest('./static/dist/js'));
});

gulp.task('js:lint', function() {
  gulp.src(['./static/src/js/**/*.js', '!./static/src/js/lib/*', 'Gulpfile.js'])
    .pipe(plumber())
      .pipe(jscs())
    .pipe(jshint())
    .pipe(jshint.reporter('default'));
});

gulp.task('js', ['js:lint', 'js:build']);

gulp.task('images', function() {
  gulp.src('./static/src/img/**/*')
    .pipe(plumber())
    .pipe(gulp.dest('./static/dist/img'))
    .pipe(reload({
      stream: true,
    }));
});

gulp.task('images:optimized', function() {
  gulp.src('./static/src/img/**/*')
    .pipe(imagemin())
    .pipe(gulp.dest('./static/dist/img'))
});

gulp.task('run', function() {
  spawn('./config/runserver.sh', ['debug'], {
    stdio: 'inherit',
  });
});

gulp.task('watch', function() {
  gulp.watch('./static/src/sass/**/*.scss', ['sass']);
  gulp.watch('./static/src/img/**/*', ['images']);
  gulp.watch('./static/src/font/**/*', ['fonts']);
  gulp.watch(['./static/src/js/**/*.js', 'Gulpfile.js'], ['js']);
});

gulp.task('build', ['sass', 'images', 'js']);
gulp.task('build:optimized', ['sass:optimized', 'images:optimized', 'js:optimized']);

gulp.task('serve', ['run', 'build'], function() {

  // Proxy over to the Flask app
  browserSync.init({
    proxy: 'localhost:5000',
    files: ['./templates/**/*'],
  });

  // add browserSync.reload to the tasks array to make
  // all browsers reload after tasks are complete.
  gulp.start(['watch']);
});

gulp.task('default', ['build']);
