# Support Vector Machine (SVM)

- **Source:** https://www.analyticsvidhya.com/blog/2021/10/support-vector-machinessvm-a-complete-guide-for-beginners/
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA > AI & ML)
- **Retrieved:** 2026-10-22


---

SVM (Support Vector Machine) is a supervised algorithm, effective for both regression and classification, though it excels in classification tasks. Popular since the 1990s, it performs well on smaller or complex datasets with minimal tuning. Before diving into SVM, ensure you’re familiar with **[Decision Trees](https://www.analyticsvidhya.com/blog/2021/08/decision-tree-algorithm/)**, Random Forest, **[Naïve Bayes](https://analyticsvidhya.com/blog/2017/09/naive-bayes-explained/)**, K-nearest neighbor, and Ensemble Modeling. In this article , you will get to know about the support vector machine

**This article was published as a part of the [Data Science Blogathon!](https://datahack.analyticsvidhya.com/blogathon/)**

A Support Vector Machine (SVM) is a **[machine learning algorithm](https://www.analyticsvidhya.com/blog/2022/01/machine-learning-algorithms/)** used for classification and regression. This finds the best line (or hyperplane) to separate data into groups, maximizing the distance between the closest points (support vectors) of each group. It can handle complex data using kernels to transform it into higher dimensions. In short, SVM helps classify data effectively.

SVM is defined such that it is defined in terms of the support vectors only, we don’t have to worry about other observations since the margin is made using the points which are closest to the hyperplane (support vectors), whereas in logistic regression the classifier is defined over all the points. Hence SVM enjoys some natural speed-ups.

Let’s understand the working of SVM using an example. Suppose we have a dataset that has two classes (green and blue). We want to classify that the new data point as either blue or green.

To classify these points, we can have many decision boundaries, but the question is which is the best and how do we find it?

**NOTE:** Since we are plotting the data points in a 2-dimensional graph we call this decision boundary a **straight line** but if we have more dimensions, we call this decision boundary a **“hyperplane”**

The best hyperplane is that plane that has the maximum distance from both the classes, and this is the main aim of SVM. This is done by finding different hyperplanes which classify the labels in the best way then it will choose the one which is farthest from the data points or the one which has a maximum margin.

Many people skip the math behind SVMs because it’s complex. Here, we’ll focus on the key steps needed to implement the algorithm, avoiding deep theoretical concepts like primal/dual formulations or Lagrange multipliers, which are more relevant for research. Let’s dive into the practical workings of SVMs.

Before getting into the nitty-gritty details of this topic first let’s understand what a dot product is.

We all know that a vector is a quantity that has magnitude as well as direction and just like numbers we can use mathematical operations such as addition, multiplication. In this section, we will try to learn about the multiplication of vectors which can be done in two ways, dot product, and cross product. The difference is only that the dot product is used to get a scalar value as a resultant whereas cross-product is used to obtain a vector again.

The dot product can be defined as the projection of one vector along with another, multiply by the product of another vector.

Here a and b are 2 vectors, to find the dot product between these 2 vectors we first find the magnitude of both the vectors and to find magnitude we use the Pythagorean theorem or the distance formula.

After finding the magnitude we simply multiply it with the cosine angle between both the vectors. Mathematically it can be written as:

**A . B = |A| cosθ \* |B|** 

Now in SVM we just need the projection of A not the magnitude of B, I’ll tell you why later. To just get the projection we can simply take the unit vector of B because it will be in the direction of B but its magnitude will be 1. Hence now the equation becomes:

**A.B = |A| cosθ \* unit vector of B**

Now let’s move to the next part and see how we will use this in SVM.

Consider a random point X and we want to know whether it lies on the right side of the plane or the left side of the plane (positive or negative).

To find this first we assume this point is a vector (X) and then we make a vector (w) which is perpendicular to the hyperplane. Let’s say the distance of vector w from origin to decision boundary is ‘c’. Now we take the projection of X vector on w.

We already know that projection of any vector or another vector is called dot-product. Hence, we take the dot product of x and w vectors. If the dot product is greater than ‘c’ then we can say that the point lies on the right side. If the dot product is less than ‘c’ then the point is on the left side and if the dot product is equal to ‘c’ then the point lies on the decision boundary.

**Reason for Perpendicular Vector (w) in SVM:**

In SVM we also have a concept of margin. In the next section, we will see how we find the equation of a hyperplane and what exactly do we need to optimize in SVM.

We all know the equation of a hyperplane is w.x+b=0 where w is a vector normal to hyperplane and b is an offset.

To classify a point as negative or positive we need to define a decision rule. We can define decision rule as:

If the value of w.x+b>0 then we can say it is a positive point otherwise it is a negative point. Now we need (w,b) such that the margin has a maximum distance. Let’s say this distance is ‘d’.

To calculate ‘d’ we need the equation of L1 and L2. For this, we will take few assumptions that the equation of L1 is **w.x+b=1** and for L2 it is **w.x+b=-1**.

**Suppose the equation of our hyperplane is 2x+y=2**:

Let’s create margin for this hyperplane,

If you multiply these equations by 10, we will see that the parallel line (red and green) gets closer to our hyperplane. For more **[clarity look at this graph](https://www.desmos.com/calculator/dvjo3vacyp)**.

We also observe that if we divide this equation by 10 then these parallel lines get bigger. Look **[at this graph](https://www.desmos.com/calculator/15dbwehq9g)**.

By this I wanted to show you that the parallel lines depend on (w,b) of our hyperplane, if we multiply the equation of hyperplane with a factor greater than 1 then the parallel lines will shrink and if we multiply with a factor less than 1, they expand.

We can now say that these lines will move as we do changes in (w,b) and this is how this gets optimized. But what is the optimization function? Let’s calculate it.

We know that the aim of SVM is to maximize this margin that means distance (d). But there are few constraints for this distance (d). Let’s look at what these constraints are.

In order to get our optimization function, there are few constraints to consider. That constraint is that “We’ll calculate the distance (d) in such a way that no positive or negative point can cross the margin line”. Let’s write these constraints mathematically:

Rather than taking 2 constraints forward, we’ll now try to simplify these two constraints into 1. We assume that negative classes have ***y=-1*** and positive classes have *****y=1**.***

We can say that for every point to be correctly classified this condition should always be true:

Suppose a green point is correctly classified that means it will follow **w.x+b>=1,** if we multiply this with **y=1** we get this same equation mentioned above. Similarly, if we do this with a red point with **y=-1** we will again get this equation**.** Hence, we can say that we need to maximize (d) such that this constraint holds true.

**Note:** this perpendicular vector should be a unit vector then only this will work. Why this should be a unit vector? This has been explained in the dot-product section. To make this ‘w’ a unit vector we divide this with the norm of ‘w’.

We already know how to find the projection of a vector on another vector. We do this by dot-product of both vectors. So let’s see how

Since x2 and x1 are support vectors and they lie on the hyperplane, hence they will follow **y<sub>i</sub>\* (2.x+b)=1** so we can write it as:

Putting equations (2) and (3) in equation (1) we get:

Hence the equation which we have to maximize is:

We have now found our optimization function but there is a catch here that we don’t find this type of perfectly linearly separable data in the industry, there is hardly any case we get this type of data and hence we fail to use this condition we proved here. The type of problem which we just studied is called **Hard Margin SVM** now we shall study soft margin which is similar to this but there are few more interesting tricks we use in **Soft Margin SVM.**

To tackle this problem what we do is modify that equation in such a way that it allows few misclassifications that means it allows few points to be wrongly classified.

We know that *max\[f(x)\]* can also be written as *min\[1/f(x)\]*, it is common practice to minimize a cost function for optimization problems; therefore, we can invert the function.

To make a soft margin equation we add 2 more terms to this equation which is **zeta** and multiply that by a **hyperparameter ‘c’**

For all the ***correctly classified*** points our **zeta** will be equal to 0 and for all the ***incorrectly classified*** points the **zeta** is simply the distance of that particular point from its correct hyperplane that means if we see the wrongly classified green points the value of **zeta** will be the distance of these points from L1 hyperplane and for wrongly classified redpoint **zeta** will be the distance of that point from L2 hyperplane.

So now we can say that our that are **SVM Error = Margin Error + Classification Error.** The higher the margin, the lower would-be margin error, and vice versa.

Let’s say you take a high value of ‘c’ =1000, this would mean that you don’t want to focus on margin error and just want a model which doesn’t misclassify any data point.

**Look at the figure below:**

If someone asks you which is a better model, the one where the margin is maximum and has 2 misclassified points or the one where the margin is very less, and all the points are correctly classified?

Well, there’s no correct answer to this question, but rather we can use *SVM Error = Margin Error + Classification Error to* justify this. If you don’t want any misclassification in the model then you can choose *figure 2*. That means we’ll increase ‘c’ to decrease Classification Error but if you want that your margin should be maximized then the value of ‘c’ should be minimized. That’s why ‘c’ is a hyperparameter and we find the optimal value of ‘c’ using GridsearchCV and cross-validation.

The most interesting feature of SVM is that it can even work with a non-linear dataset and for this, we use “Kernel Trick” which makes it easier to classifies the points. Suppose we have a dataset like this:

Here we see we cannot draw a single line or say hyperplane which can classify the points correctly. So what we do is try converting this lower dimension space to a higher dimension space using some quadratic functions which will allow us to find a decision boundary that clearly divides the data points. These functions which help us do this are called Kernels and which kernel to use is purely determined by hyperparameter tuning.

Some kernel functions which you can use in SVM are given below:

Following is the formula for the polynomial kernel:

So we basically need to find X<sub>1</sub><sup>2</sup> , X<sub>2</sub><sup>2</sup> and X1.X2, and now we can see that 2 dimensions got converted into 5 dimensions.

We can use it as the proxy for neural networks. Equation is:

It is just taking your input, mapping them to a value of 0 and 1 so that they can be separated by a simple straight line.

Image Source: https://dataaspirant.com/svm-kernels/#t-1608054630725

What it actually does is to create non-linear combinations of our features to lift your samples onto a higher-dimensional feature space where we can use a linear decision boundary to separate your classes It is the most used kernel in SVM classifications, the following formula explains it mathematically:

where,

It is mainly used for eliminating the cross term in mathematical functions. Following is the formula of the Bessel function kernel:

It performs well on multidimensional regression problems. The formula for this kernel function is:

I am well aware of the fact that you must be having this doubt about how to decide which kernel function will work efficiently for your dataset. It is necessary to choose a good kernel function because the performance of the model depends on it.

**Here are the Points to choose the right Kernal:**

Let’s understand this with the help of an example, for simplicity I’ll only take 2 features that mean 2 dimensions only. In the figure below I have plotted the decision boundary of a linear SVM on 2 features of the iris dataset:

Here we see that a linear kernel works fine on this dataset, but now let’s see how will RBF kernel work.

We can observe that both the kernels give similar results, both work well with our dataset but which one should we choose? Linear SVM is a parametric model. A Parametric Model is a concept used to describe a model in which all its data is represented within its parameters. In short, the only information needed to predict the future from the current value is the parameters.

**Here are some points you should go through:**

So for this kind of dataset, we can use RBF without even a second thought because it makes decision boundary like this:

For implementation on a dataset, we will be using the Income Evaluation dataset, which has information about an individual’s personal life and an output of 50K or \<=50. The **[dataset can be found here](https://www.kaggle.com/lodetomasi1995/income-classification)**.

The task here is to classify the income of an individual when given the required inputs about his personal life.

First, let’s import all required libraries.

```
# Import all relevant libraries
from sklearn.svm import SVC
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn import preprocessing
import warnings
warnings.filterwarnings("ignore")
Now let’s read the dataset and look at the columns to understand the information better.
df = pd.read_csv('income_evaluation.csv')
df.head()
```
I have already done the data preprocessing part and you can look whole code [**here**](https://github.com/AnshulSaini17/Income_evaluation/blob/main/Income_Evalutation.ipynb). Here my main aim is to tell you how to implement SVM on python.

Now for training and testing our model, the data has to be divided into train and test data.

We will also scale the data to lie between 0 and 1.

`# Split dataset into test and train data`
Now let’s go ahead with defining the Support vector Classifier along with its hyperparameters. Next, we will fit this model on the training data.

```
#Define support vector classifier with hyperparameters
X_train, X_test, y_train, y_test = train_test_split(df.drop(‘income’, axis=1),df[‘income’], test_size=0.2)
svc.fit(X_train,y_train)
svc = SVC(random_state=101)
accuracies = cross_val_score(svc,X_train,y_train,cv=5)
print("Train Score:"np.mean(accuracies))
printf("Test Score:"svc.score(X_test,y_test))
```
The model has been trained and we can now observe the outputs as well.

Below, you can see the accuracy of the test and train dataset

You can even hyper tune your model by the following code:

```
grid = {
    'C':[0.01,0.1,1,10],
    'kernel' : ["linear","poly","rbf","sigmoid"],
    'degree' : [1,3,5,7],
    'gamma' : [0.01,1]
}
 svm  = SVC ()
svm_cv = GridSearchCV(svm, grid, cv = 5)
svm_cv.fit(X_train,y_train)
print("Best Parameters:",svm_cv.best_params_)
print("Train Score:",svm_cv.best_score_)
print("Test Score:",svm_cv.score(X_test,y_test))
```
The dataset is pretty big and hence it will take time to get trained, for this reason, I can’t paste the result of the above code here because SVM doesn’t perform well with big datasets, it takes a long time to get trained.

A popular and reliable supervised machine learning technique called Support Vector Machine (SVM) was first created for classification tasks, though it can also be modified to solve regression issues. The goal of SVM is to locate in the feature space the optimal separation hyperplane between classes. Checkout these feature :

In this article, we looked at a very powerful machine learning algorithm, Support Vector Machine in detail. I discussed its concept of working, math intuition behind SVM, implementation in python, the tricks to classify non-linear datasets, Pros and cons, and finally, we solved a problem with the help of SVM. Also you will get some insights on SVM in Machine Learning.

A. A machine learning model that finds the best boundary to separate different groups of data points.

A. It draws the widest possible gap between classes, using key points called support vectors for decision-making.

A. The steps of the SVM algorithm involve: (1) selecting the appropriate kernel function, (2) defining the parameters and constraints, (3) solving the optimization problem to find the optimal hyperplane, and (4) making predictions based on the learned model.

A. Detecting spam emails by sorting them into “spam” or “not spam” based on their features.

I think there is a need to validate the code that has been shared here. There are many gaps and errors when executing. Perhaps you could evaluate this on google collaboratory before submitting.

hello sir, you explained SVM very well, thank you

Very well explained. Thank you 🙏