// components/Features.js
const features = [
    { title: 'Fast Performance', description: 'Experience quick response times with optimized endpoints.' },
    { title: 'Secure Authentication', description: 'Ensure data safety with robust authentication mechanisms.' },
    { title: 'Comprehensive Documentation', description: 'Access detailed guides and references to get started.' },
];

const Features = () => (
    <section className="container mx-auto py-16">
        <h2 className="text-3xl font-semibold text-center text-orange-300 mb-8">Our API Features</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
                <div key={index} className="bg-gray-800 p-6 rounded-lg shadow-md">
                    <h3 className="text-xl font-semibold text-orange-500 mb-4">{feature.title}</h3>
                    <p className="text-gray-300">{feature.description}</p>
                </div>
            ))}
        </div>
    </section>
);

export default Features;
