# Build a Simple Fitness App

In this tutorial, we will build a simple fitness app similar to Fitbud. The app will allow users to track their workouts, set goals, and monitor their progress. We will use JavaScript and a few other technologies to create this app.

## Step 1: Setting Up the Project

First, let's set up our project. Create a new directory for your project and initialize a new Node.js project:

```bash
mkdir fitness-app
cd fitness-app
npm init -y
```

Next, install the necessary dependencies:

```bash
npm install express body-parser mongoose
```

## Step 2: Creating the Server

We will use Express to create our server. Create a new file called `server.js` and add the following code:

```javascript
const express = require('express');
const bodyParser = require('body-parser');
const mongoose = require('mongoose');

const app = express();
const port = 3000;

app.use(bodyParser.json());

mongoose.connect('mongodb://localhost/fitness-app', { useNewUrlParser: true, useUnifiedTopology: true });

app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
});
```

## Step 3: Creating the User Model

We will use Mongoose to create our user model. Create a new file called `models/User.js` and add the following code:

```javascript
const mongoose = require('mongoose');

const userSchema = new mongoose.Schema({
  username: { type: String, required: true, unique: true },
  password: { type: String, required: true },
  workouts: [{ type: mongoose.Schema.Types.ObjectId, ref: 'Workout' }]
});

const User = mongoose.model('User', userSchema);

module.exports = User;
```

## Step 4: Creating the Workout Model

Next, create a new file called `models/Workout.js` and add the following code:

```javascript
const mongoose = require('mongoose');

const workoutSchema = new mongoose.Schema({
  user: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
  date: { type: Date, required: true },
  exercises: [{
    name: { type: String, required: true },
    sets: { type: Number, required: true },
    reps: { type: Number, required: true },
    weight: { type: Number, required: true }
  }]
});

const Workout = mongoose.model('Workout', workoutSchema);

module.exports = Workout;
```

## Step 5: Creating the User Routes

Create a new file called `routes/user.js` and add the following code:

```javascript
const express = require('express');
const router = express.Router();
const User = require('../models/User');

router.post('/register', async (req, res) => {
  try {
    const user = new User(req.body);
    await user.save();
    res.status(201).send(user);
  } catch (error) {
    res.status(400).send(error);
  }
});

router.post('/login', async (req, res) => {
  try {
    const user = await User.findOne({ username: req.body.username, password: req.body.password });
    if (!user) {
      return res.status(401).send({ error: 'Invalid credentials' });
    }
    res.send(user);
  } catch (error) {
    res.status(400).send(error);
  }
});

module.exports = router;
```

## Step 6: Creating the Workout Routes

Create a new file called `routes/workout.js` and add the following code:

```javascript
const express = require('express');
const router = express.Router();
const Workout = require('../models/Workout');

router.post('/', async (req, res) => {
  try {
    const workout = new Workout(req.body);
    await workout.save();
    res.status(201).send(workout);
  } catch (error) {
    res.status(400).send(error);
  }
});

router.get('/:userId', async (req, res) => {
  try {
    const workouts = await Workout.find({ user: req.params.userId });
    res.send(workouts);
  } catch (error) {
    res.status(400).send(error);
  }
});

module.exports = router;
```

## Step 7: Integrating the Routes

Update the `server.js` file to include the user and workout routes:

```javascript
const express = require('express');
const bodyParser = require('body-parser');
const mongoose = require('mongoose');
const userRoutes = require('./routes/user');
const workoutRoutes = require('./routes/workout');

const app = express();
const port = 3000;

app.use(bodyParser.json());

mongoose.connect('mongodb://localhost/fitness-app', { useNewUrlParser: true, useUnifiedTopology: true });

app.use('/users', userRoutes);
app.use('/workouts', workoutRoutes);

app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
});
```

## Step 8: Testing the API

You can use a tool like Postman to test the API. Here are some example requests:

- Register a new user:
  - POST http://localhost:3000/users/register
  - Body: `{ "username": "testuser", "password": "password123" }`

- Login a user:
  - POST http://localhost:3000/users/login
  - Body: `{ "username": "testuser", "password": "password123" }`

- Create a new workout:
  - POST http://localhost:3000/workouts
  - Body: `{ "user": "userId", "date": "2021-01-01", "exercises": [{ "name": "Squat", "sets": 3, "reps": 10, "weight": 100 }] }`

- Get workouts for a user:
  - GET http://localhost:3000/workouts/userId

## Conclusion

Congratulations! You have built a simple fitness app similar to Fitbud. You can now extend this app by adding more features such as goal tracking, progress monitoring, and more. Happy coding!
