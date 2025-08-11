FROM ruby:3.3-alpine

RUN apk add --no-cache build-base mariadb-dev curl

WORKDIR /app
COPY Gemfile Gemfile.lock /app/
RUN bundle install
COPY app.rb /app/app.rb

EXPOSE 4567
CMD ["ruby", "app.rb"]


