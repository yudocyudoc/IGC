within;

model WrapperCS01
  Modelica.Blocks.Sources.Constant arrivals(k=3);
  IGCMolecules.AcceptedSource source;
  IGCMolecules.BoundedQueue stage0(maxThroughput=2, responseTime=1);
  IGCMolecules.DeliveryCounter counter;
  output Real delivered;
  output Real waiting;
equation
  connect(arrivals.y, source.externalRate);
  connect(source.outflow, stage0.arrival);
  connect(stage0.completed, counter.arrival);
  delivered = counter.total;
  waiting = stage0.waiting;
end WrapperCS01;

model WrapperCS02
  Modelica.Blocks.Sources.Constant arrivals(k=3);
  IGCMolecules.AcceptedSource source;
  IGCMolecules.BoundedQueue stage0(maxThroughput=2, responseTime=1);
  IGCMolecules.BoundedQueue stage1(maxThroughput=2, responseTime=1);
  IGCMolecules.DeliveryCounter counter;
  output Real delivered;
  output Real waiting0;
  output Real waiting1;
equation
  connect(arrivals.y, source.externalRate);
  connect(source.outflow, stage0.arrival);
  connect(stage0.completed, stage1.arrival);
  connect(stage1.completed, counter.arrival);
  delivered = counter.total;
  waiting0 = stage0.waiting;
  waiting1 = stage1.waiting;
end WrapperCS02;
