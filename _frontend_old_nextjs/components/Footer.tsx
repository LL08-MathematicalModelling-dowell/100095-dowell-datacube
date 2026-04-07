import { FaGithub, FaTwitter, FaLinkedin } from 'react-icons/fa'

export const Footer = () => {
    return (
        <footer className="py-8 bg-gray-900">
            <div className="max-w-7xl mx-auto px-4 flex flex-col md:flex-row items-center justify-between">
                <p className="text-gray-500 text-sm">
                    © {new Date().getFullYear()} DataCube Inc. All rights reserved.
                </p>
                <div className="flex space-x-4 mt-4 md:mt-0">
                    {[FaGithub, FaTwitter, FaLinkedin].map((Icon, i) => (
                        <Icon
                            key={i}
                            size={20}
                            className="text-gray-500 hover:text-pink-400 transition"
                        />
                    ))}
                </div>
            </div>
        </footer>
    )
}