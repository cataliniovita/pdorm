FROM ruby:3.3-alpine

RUN apk add --no-cache build-base postgresql-dev curl

WORKDIR /app
COPY Gemfile Gemfile.lock /app/
RUN bundle install
COPY app.rb /app/app.rb

EXPOSE 4567
CMD ["ruby", "app.rb"]


