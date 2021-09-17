## PIS model overview

This is a small flask application which implements a visual overview of the PIS network. It tries to match the visual representation as defined by SBGN as much as possible without too much custom rendering.

**Please note that the backend and the search interface are only provisional as the code is intended to be integrated into a larger web application.**


### Requirements

-  docker
-  docker-compose


### How to run

The following command

```sh
$ docker-compose up --build
```

will build the images and run the container. The application is now available for testing at [http://localhost:5005](http://localhost:5005).


###  Authors

[Vid Podpečan](vid.podpecan@ijs.si)


### License

MIT
