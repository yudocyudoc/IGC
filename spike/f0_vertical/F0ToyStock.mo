within ;
model F0ToyStock
  // Synthetic engineering fixture only; not a model of a real business.
  Real orderStock(start=0, fixed=true);
  parameter Real syntheticArrivalRate = 3;
  parameter Real syntheticCompletionRate = 1;
equation
  der(orderStock) = syntheticArrivalRate - syntheticCompletionRate;
end F0ToyStock;
