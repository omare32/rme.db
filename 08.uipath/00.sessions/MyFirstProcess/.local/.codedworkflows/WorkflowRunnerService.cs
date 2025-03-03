using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using UiPath.CodedWorkflows;
using UiPath.CodedWorkflows.Interfaces;
using UiPath.Activities.Contracts;
using MyFirstProcess;

[assembly: WorkflowRunnerServiceAttribute(typeof(MyFirstProcess.WorkflowRunnerService))]
namespace MyFirstProcess
{
    public class WorkflowRunnerService
    {
        private readonly ICodedWorkflowServices _services;
        public WorkflowRunnerService(ICodedWorkflowServices services)
        {
            _services = services;
        }

        /// <summary>
        /// Invokes the Workflow.cs
        /// </summary>
        public void Workflow()
        {
            var result = _services.WorkflowInvocationService.RunWorkflow(@"Workflow.cs", new Dictionary<string, object>{}, default, default, default, GetAssemblyName());
        }

        /// <summary>
        /// Invokes the ERB/ERB_Login.xaml
        /// </summary>
        public void ERB_Login()
        {
            var result = _services.WorkflowInvocationService.RunWorkflow(@"ERB\ERB_Login.xaml", new Dictionary<string, object>{}, default, default, default, GetAssemblyName());
        }

        /// <summary>
        /// Invokes the StateMachine.xaml
        /// </summary>
        public void StateMachine()
        {
            var result = _services.WorkflowInvocationService.RunWorkflow(@"StateMachine.xaml", new Dictionary<string, object>{}, default, default, default, GetAssemblyName());
        }

        /// <summary>
        /// Invokes the Main.xaml
        /// </summary>
        public void Main()
        {
            var result = _services.WorkflowInvocationService.RunWorkflow(@"Main.xaml", new Dictionary<string, object>{}, default, default, default, GetAssemblyName());
        }

        private string GetAssemblyName()
        {
            var assemblyProvider = _services.Container.Resolve<ILibraryAssemblyProvider>();
            return assemblyProvider.GetLibraryAssemblyName(GetType().Assembly);
        }
    }
}